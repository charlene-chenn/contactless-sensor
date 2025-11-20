import cv2
import numpy as np
import json
import sys
sys.path.append('src')
from camera import Camera

# Global variables
hsv_color = None
h_range, s_range, v_range = 10, 50, 50

def mouse_callback(event, x, y, flags, param):
    """
    Mouse callback function to get the HSV color of the clicked point.
    """
    global hsv_color
    if event == cv2.EVENT_LBUTTONDOWN:
        frame = param
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Average the color of a small region
        region = hsv_frame[y-2:y+2, x-2:x+2]
        hsv_color = np.mean(region, axis=(0, 1)).astype(int)
        print(f"Selected HSV color: {hsv_color}")

def main():
    """
    Main function for the color calibration utility.
    """
    global hsv_color, h_range, s_range, v_range

    # Load config to get camera index
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    camera_index = Camera.select_camera(config)
    if camera_index is None:
        return

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Initialize camera
    camera = Camera(camera_index)
    if not camera.initialize():
        print(f"Error: Could not open camera with index {camera_index}.")
        return

    cv2.namedWindow("Camera Feed")
    cv2.setMouseCallback("Camera Feed", mouse_callback)

    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("H Range", "Trackbars", h_range, 127, lambda x: None)
    cv2.createTrackbar("S Range", "Trackbars", s_range, 127, lambda x: None)
    cv2.createTrackbar("V Range", "Trackbars", v_range, 127, lambda x: None)


    print("Click on the object to select its color.")
    print("Adjust the trackbars to fine-tune the mask.")
    print("Press 's' to save the color for the 'pivot' ball.")
    print("Press 'm' to save the color for the 'moving' ball.")
    print("Press 'r' to save the color for the 'rod'.")
    print("Press 'q' to quit.")

    while True:
        ret, frame = camera.read_frame()
        if not ret:
            break

        # Pass the frame to the mouse callback
        cv2.setMouseCallback("Camera Feed", mouse_callback, frame)

        cv2.imshow("Camera Feed", frame)

        if hsv_color is not None:
            h_range = cv2.getTrackbarPos("H Range", "Trackbars")
            s_range = cv2.getTrackbarPos("S Range", "Trackbars")
            v_range = cv2.getTrackbarPos("V Range", "Trackbars")

            lower_bound = np.array([max(0, hsv_color[0] - h_range), max(0, hsv_color[1] - s_range), max(0, hsv_color[2] - v_range)])
            upper_bound = np.array([min(179, hsv_color[0] + h_range), min(255, hsv_color[1] + s_range), min(255, hsv_color[2] + v_range)])
            
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
            cv2.imshow("Mask", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key in [ord('s'), ord('m'), ord('r')]:
            if hsv_color is not None:
                
                lower_bound_val = [int(max(0, hsv_color[0] - h_range)), int(max(0, hsv_color[1] - s_range)), int(max(0, hsv_color[2] - v_range))]
                upper_bound_val = [int(min(179, hsv_color[0] + h_range)), int(min(255, hsv_color[1] + s_range)), int(min(255, hsv_color[2] + v_range))]

                if key == ord('s'):
                    config['ball_colors']['pivot']['lower'] = lower_bound_val
                    config['ball_colors']['pivot']['upper'] = upper_bound_val
                    print(f"Saved color for 'pivot' ball to config.json")
                elif key == ord('m'):
                    config['ball_colors']['moving']['lower'] = lower_bound_val
                    config['ball_colors']['moving']['upper'] = upper_bound_val
                    print(f"Saved color for 'moving' ball to config.json")
                elif key == ord('r'):
                    config['rod_color']['lower'] = lower_bound_val
                    config['rod_color']['upper'] = upper_bound_val
                    print(f"Saved color for 'rod' to config.json")

                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
                
            else:
                print("Please select a color first by clicking on the object.")


    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
