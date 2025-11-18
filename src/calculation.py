import numpy as np

def calculate_angle(pivot_ball_center: tuple, moving_ball_center: tuple):
    """
    Calculates the angle of the moving ball relative to the pivot ball and the vertical.

    :param pivot_ball_center: Coordinates (x, y) of the pivot ball.
    :param moving_ball_center: Coordinates (x, y) of the moving ball.
    :return: The angle in degrees, where 0 is vertical, positive is to the right, and negative is to the left.
    """
    x_pivot, y_pivot = pivot_ball_center
    x_moving, y_moving = moving_ball_center

    # Calculate the difference in coordinates
    dx = x_moving - x_pivot
    dy = y_moving - y_pivot

    # Calculate the angle using arctan2.
    # arctan2(dx, dy) gives the angle from the positive y-axis.
    angle_radians = np.arctan2(dx, dy)
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees
