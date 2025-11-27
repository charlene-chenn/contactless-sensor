import cv2
import numpy as np

def create_mask(image: np.ndarray, lower_hsv: np.ndarray, upper_hsv: np.ndarray):
    """
    Creates a mask for a given color range in an image.

    :param image: The image to process.
    :param lower_hsv: The lower bound of the color to search for in HSV.
    :param upper_hsv: The upper bound of the color to search for in HSV.
    :return: The generated mask.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    return mask

def find_ball(image: np.ndarray, lower_hsv: np.ndarray, upper_hsv: np.ndarray):
    """
    Finds a ball of a given color in an image.

    :param image: The image to search in.
    :param lower_hsv: The lower bound of the color to search for in HSV.
    :param upper_hsv: The upper bound of the color to search for in HSV.
    :return: A tuple containing the center of the ball and the mask, or (None, mask) if no ball is found.
    """
    mask = create_mask(image, lower_hsv, upper_hsv)

    # Morphological operations to remove noise and fill gaps
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, mask

    # Find the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the center of the contour
    moments = cv2.moments(largest_contour)
    if moments["m00"] == 0:
        return None, mask
        
    center_x = int(moments["m10"] / moments["m00"])
    center_y = int(moments["m01"] / moments["m00"])

    return (center_x, center_y), mask

def find_rod(image: np.ndarray, lower_hsv: np.ndarray, upper_hsv: np.ndarray):
    """
    Finds a colored rod in an image.

    :param image: The image to search in.
    :param lower_hsv: The lower bound of the color to search for in HSV.
    :param upper_hsv: The upper bound of the color to search for in HSV.
    :return: The endpoints of the rod, or None if no rod is found.
    """
    mask = create_mask(image, lower_hsv, upper_hsv)

    # Morphological operations to remove noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Find lines using Hough Line Transform
    lines = cv2.HoughLinesP(mask, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=10)

    if lines is None:
        return None

    # Find the longest line
    longest_line = None
    max_length = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length > max_length:
            max_length = length
            longest_line = ((x1, y1), (x2, y2))

    return longest_line
