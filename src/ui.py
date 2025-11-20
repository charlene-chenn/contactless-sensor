import cv2
import numpy as np
from .calculation import calculate_angle, calculate_rod_angle

def display_frame(frame: np.ndarray, pivot_center: tuple = None, moving_center: tuple = None, rod_endpoints: tuple = None, mask: np.ndarray = None):
    """
    Displays the camera frame with optional overlays for ball centers and mask.

    :param frame: The original camera frame.
    :param pivot_center: Coordinates (x, y) of the pivot ball center.
    :param moving_center: Coordinates (x, y) of the moving ball center.
    :param rod_endpoints: Endpoints of the detected rod.
    :param mask: The mask generated during ball detection.
    """
    display_image = frame.copy()

    if rod_endpoints:
        (x1, y1), (x2, y2) = rod_endpoints
        cv2.line(display_image, (x1, y1), (x2, y2), (0, 255, 255), 2) # Yellow line for the rod
        angle = calculate_rod_angle(rod_endpoints)
        cv2.putText(display_image, f"Angle: {angle:.2f} degrees", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw vertical line from pivot
        pivot_x, pivot_y = (x1, y1) if y1 < y2 else (x2, y2)
        cv2.line(display_image, (pivot_x, pivot_y), (pivot_x, frame.shape[0]), (255, 255, 255), 1)

    else:
        if pivot_center:
            cv2.circle(display_image, pivot_center, 5, (0, 255, 0), -1) # Green circle for pivot ball
            cv2.putText(display_image, f"Pivot: {pivot_center}", (pivot_center[0] + 10, pivot_center[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw vertical line
            cv2.line(display_image, pivot_center, (pivot_center[0], frame.shape[0]), (255, 255, 255), 1) # White vertical line
        else:
            cv2.putText(display_image, "Pivot ball not detected", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


        if moving_center:
            cv2.circle(display_image, moving_center, 5, (0, 0, 255), -1) # Red circle for moving ball
            cv2.putText(display_image, f"Moving: {moving_center}", (moving_center[0] + 10, moving_center[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        else:
            cv2.putText(display_image, "Moving ball not detected", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


        if pivot_center and moving_center:
            # Draw line between balls
            cv2.line(display_image, pivot_center, moving_center, (255, 0, 0), 2) # Blue line connecting balls

            # Calculate and display angle
            angle = calculate_angle(pivot_center, moving_center)
            cv2.putText(display_image, f"Angle: {angle:.2f} degrees", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


    cv2.imshow("Camera Feed", display_image)

    if mask is not None:
        cv2.imshow("Ball Mask", mask)


def handle_input():
    """
    Handles keyboard input for UI.

    :return: True if 'q' is pressed, indicating quit.
    """
    key = cv2.waitKey(1) & 0xFF
    return key == ord('q')


def destroy_windows():
    """
    Destroys all OpenCV created windows.
    """
    cv2.destroyAllWindows()
