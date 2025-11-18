import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from calculation import calculate_angle

class TestCalculation(unittest.TestCase):

    def test_calculate_angle(self):
        # Test case 1: Moving ball is directly below the pivot ball
        self.assertAlmostEqual(calculate_angle((100, 100), (100, 200)), 0.0)

        # Test case 2: Moving ball is to the right of the pivot ball
        self.assertAlmostEqual(calculate_angle((100, 100), (200, 100)), 90.0)

        # Test case 3: Moving ball is to the left of the pivot ball
        self.assertAlmostEqual(calculate_angle((100, 100), (0, 100)), -90.0)

        # Test case 4: 45 degrees
        self.assertAlmostEqual(calculate_angle((100, 100), (200, 200)), 45.0)

        # Test case 5: -45 degrees
        self.assertAlmostEqual(calculate_angle((100, 100), (0, 200)), -45.0)

if __name__ == '__main__':
    unittest.main()
