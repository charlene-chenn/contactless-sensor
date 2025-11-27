import argparse
import json

import numpy as np

from .calculation import calculate_angle, calculate_rod_angle
from .camera import Camera
from .detection import find_ball, find_rod
from .ui import destroy_windows, display_frame, handle_input


def main():
    """
    Main function for the contactless sensor application.
    """
    parser = argparse.ArgumentParser(description='Contactless sensor application.')
    parser.add_argument('--output-angle', action='store_true', help='Output the angle to the console as a raw float.')
    parser.add_argument('--no-ui', action='store_true', help='Disable the graphical user interface.')
    args = parser.parse_args()

    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    camera_index = config.get('camera_index', 0)
    mode = config.get('mode', 'two_balls')

    # Initialize camera
    camera = Camera(camera_index)
    if not camera.initialize():
        print(f"Could not open camera with index {camera_index} from config.")
        camera_index = Camera.select_camera(config)
        if camera_index is None:
            return

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

        camera = Camera(camera_index)
        if not camera.initialize():
            print(f"Error: Could not open camera with index {camera_index}.")
            return

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

    try:
        while True:
            # Read frame
            ret, frame = camera.read_frame()
            if not ret:
                break

            angle = None
            if mode == 'two_balls':
                # Detect balls
                pivot_center, _ = find_ball(frame, lower_pivot_hsv, upper_pivot_hsv)
                moving_center, moving_mask = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
                if pivot_center and moving_center:
                    angle = calculate_angle(pivot_center, moving_center)
                if not args.no_ui:
                    # Pass the moving ball's mask to the UI for debugging
                    display_frame(frame, pivot_center=pivot_center, moving_center=moving_center, mask=moving_mask)

            elif mode == 'rod_and_ball':
                rod_endpoints = find_rod(frame, lower_rod_hsv, upper_rod_hsv)
                # TODO: The mask for the rod or second ball could also be displayed
                moving_center, moving_mask = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
                if rod_endpoints:
                    angle = calculate_rod_angle(rod_endpoints)
                if not args.no_ui:
                    display_frame(frame, moving_center=moving_center, rod_endpoints=rod_endpoints, mask=moving_mask)

            if args.output_angle and angle is not None:
                print(f"{angle:.2f}")

            # Handle input for UI
            if not args.no_ui:
                if handle_input():
                    break
    except KeyboardInterrupt:
        # This allows the main loop to be stopped with Ctrl+C when running without UI
        pass
    finally:
        # Release resources
        camera.release()
        if not args.no_ui:
            destroy_windows()


if __name__ == "__main__":
    main()
