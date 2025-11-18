import cv2
import numpy as np

def find_ball(image: np.ndarray, lower_hsv: np.ndarray, upper_hsv: np.ndarray):
    """
    Finds a ball of a given color in an image.

    :param image: The image to search in.
    :param lower_hsv: The lower bound of the color to search for in HSV.
    :param upper_hsv: The upper bound of the color to search for in HSV.
    :return: The center of the ball in image coordinates, or None if no ball is found.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Find the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the center of the contour
    moments = cv2.moments(largest_contour)
    if moments["m00"] == 0:
        return None
        
    center_x = int(moments["m10"] / moments["m00"])
    center_y = int(moments["m01"] / moments["m00"])

    return (center_x, center_y)
