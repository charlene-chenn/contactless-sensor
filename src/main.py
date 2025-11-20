import json
import numpy as np
import cv2
from .camera import Camera
from .detection import find_ball, find_rod
from .ui import display_frame, handle_input, destroy_windows

def get_available_cameras():
    """
    Gets a list of available camera devices.
    :return: A list of available camera indices.
    """
    available_cameras = []
    index = 0
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        available_cameras.append(index)
        cap.release()
        index += 1
    return available_cameras

def main():
    """
    Main function for the contactless sensor application.
    """
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    camera_index = config.get('camera_index', 0)
    mode = config.get('mode', 'two_balls')
    
    # Initialize camera
    camera = Camera(camera_index)
    if not camera.initialize():
        print(f"Could not open camera with index {camera_index} from config.")
        available_cameras = get_available_cameras()
        if not available_cameras:
            print("Error: No cameras found.")
            return

        print("Available cameras:", available_cameras)
        camera_index_str = input(f"Select a camera index to use: ")
        try:
            camera_index = int(camera_index_str)
            if camera_index not in available_cameras:
                print("Invalid camera index. Exiting.")
                return
        except ValueError:
            print("Invalid input. Exiting.")
            return
        
        config['camera_index'] = camera_index
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

    while True:
        # Read frame
        ret, frame = camera.read_frame()
        if not ret:
            break

        if mode == 'two_balls':
            # Detect balls
            pivot_center = find_ball(frame, lower_pivot_hsv, upper_pivot_hsv)
            moving_center = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
            display_frame(frame, pivot_center=pivot_center, moving_center=moving_center)
        
        elif mode == 'rod_and_ball':
            rod_endpoints = find_rod(frame, lower_rod_hsv, upper_rod_hsv)
            moving_center = find_ball(frame, lower_moving_hsv, upper_moving_hsv)
            display_frame(frame, moving_center=moving_center, rod_endpoints=rod_endpoints)

        # Handle input
        if handle_input():
            break

    # Release resources
    camera.release()
    destroy_windows()

if __name__ == "__main__":
    main()
