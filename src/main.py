import argparse
import json
import time

import numpy as np
import serial
from scipy import signal

from .calculation import calculate_angle, calculate_rod_angle
from .camera import Camera
from .detection import find_ball, find_rod
from .ui import destroy_windows, display_frame, handle_input


def main():
    """
    Main function for the contactless sensor application.
    """
    parser = argparse.ArgumentParser(description='Contactless sensor application.')
    parser.add_argument("--side", type=str, required=True, choices=["left", "right"], help="Tunnel side.")
    parser.add_argument('--output', type=str, choices=['angle', 'windspeed'], help='Choose the output type to print to the console.')
    parser.add_argument('--no-ui', action='store_true', help='Disable the graphical user interface.')
    args = parser.parse_args()

    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    # --- Camera and Hardware Configuration ---
    camera_index = config.get('camera_index', 0)
    camera_fps = config.get('camera_fps', 30)
    mode = config.get('mode', 'two_balls')

    # --- Detection Parameters ---
    ball_colors = config.get('ball_colors', {})
    pivot_color = ball_colors.get('pivot', {})
    moving_color = ball_colors.get('moving', {})
    rod_color = config.get('rod_color', {})
    lower_pivot_hsv = np.array(pivot_color.get('lower', [0, 0, 0]))
    upper_pivot_hsv = np.array(pivot_color.get('upper', [179, 255, 255]))
    lower_moving_hsv = np.array(moving_color.get('lower', [0, 0, 0]))
    upper_moving_hsv = np.array(moving_color.get('upper', [179, 255, 255]))
    lower_rod_hsv = np.array(rod_color.get('lower', [0, 0, 0]))
    upper_rod_hsv = np.array(rod_color.get('upper', [179, 255, 255]))

    # --- Processing and UI Parameters ---
    k = config.get('conversion_params', {}).get(args.side, {}).get('scale_constant', 1.0)
    filter_params = config.get('butterworth_filter', {}).get(args.side, {})
    arrow_scale = config.get('ui', {}).get('arrow_scale_factor', 10)

    # Initialize camera
    camera = Camera(camera_index, fps=camera_fps)
    camera.initialize()  # Assuming this is always successful after potential selection

    # Initialize serial communication
    ser = None
    try:
        ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
        print("Serial port /dev/serial0 opened successfully.")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")

    # Initialize filter for real-time processing
    sos, zi = None, None
    if filter_params:
        sos = signal.butter(filter_params['order'], filter_params['cutoff_hz'], 'low', fs=camera_fps, output='sos')
        zi = signal.sosfilt_zi(sos)

    # Initialize FPS calculation variables
    prev_time = 0
    display_fps = 0

    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                break

            angle, wind_speed, smoothed_wind_speed = None, None, None
            pivot_center, moving_center, rod_endpoints, moving_mask = None, None, None, None

            if mode == 'two_balls':
                pivot_center, _ = find_ball(frame, lower_pivot_hsv, upper_pivot_hsv)
                moving_center, moving_mask = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
                if pivot_center and moving_center:
                    angle = calculate_angle(pivot_center, moving_center)

            elif mode == 'rod_and_ball':
                rod_endpoints = find_rod(frame, lower_rod_hsv, upper_rod_hsv)
                moving_center, moving_mask = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
                if rod_endpoints:
                    angle = calculate_rod_angle(rod_endpoints)

            # Process angle to get wind speed
            if angle is not None:
                wind_speed = k * np.sqrt(np.abs(np.tan(np.deg2rad(angle))))
                if sos is not None:
                    smoothed_output, zi = signal.sosfilt(sos, [wind_speed], zi=zi)
                    smoothed_wind_speed = smoothed_output[0]

            # Calculate and smooth FPS
            current_time = time.time()
            if prev_time > 0:
                fps = 1 / (current_time - prev_time)
                display_fps = 0.9 * display_fps + 0.1 * fps
            prev_time = current_time

            # Output to console if requested
            if args.output == 'angle' and angle is not None:
                output_str = f"{angle:.2f}"
                print(output_str)
                if ser:
                    ser.write((output_str + '\n').encode())
            elif args.output == 'windspeed' and smoothed_wind_speed is not None:
                output_str = f"{smoothed_wind_speed:.2f}"
                print(output_str)
                if ser:
                    ser.write((output_str + '\n').encode())

            # Display UI if not disabled
            if not args.no_ui:
                display_frame(frame, pivot_center=pivot_center, moving_center=moving_center,
                              rod_endpoints=rod_endpoints, mask=moving_mask, angle=angle,
                              wind_speed=smoothed_wind_speed, arrow_scale=arrow_scale, fps=display_fps)
                if handle_input():
                    break

    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        if not args.no_ui:
            destroy_windows()


if __name__ == "__main__":
    main()
