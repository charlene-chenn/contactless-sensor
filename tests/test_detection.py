import unittest
import numpy as np
import cv2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from detection import find_ball

class TestDetection(unittest.TestCase):

    def test_find_ball(self):
        # Create a black image
        image = np.zeros((200, 200, 3), dtype=np.uint8)

        # Draw a red circle
        center = (100, 100)
        radius = 20
        color_bgr = (0, 0, 255)
        cv2.circle(image, center, radius, color_bgr, -1)

        # Convert color to HSV
        color_hsv = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]

        # Define a color range for red
        h, s, v = color_hsv
        lower_hsv = np.array([h - 10, s - 50, v - 50])
        upper_hsv = np.array([h + 10, 255, 255])

        # Find the ball
        ball_center = find_ball(image, lower_hsv, upper_hsv)

        # Check if the center is correct
        self.assertIsNotNone(ball_center)
        self.assertAlmostEqual(ball_center[0], center[0], delta=1)
        self.assertAlmostEqual(ball_center[1], center[1], delta=1)

    def test_find_ball_no_ball(self):
        # Create a black image
        image = np.zeros((200, 200, 3), dtype=np.uint8)

        # Define a color range for red
        lower_hsv = np.array([0, 100, 100])
        upper_hsv = np.array([10, 255, 255])

        # Find the ball
        ball_center = find_ball(image, lower_hsv, upper_hsv)

        # Check that no ball is found
        self.assertIsNone(ball_center)

if __name__ == '__main__':
    unittest.main()
