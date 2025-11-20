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

def calculate_rod_angle(rod_endpoints: tuple):
    """
    Calculates the angle of the rod relative to the vertical.

    :param rod_endpoints: A tuple containing two endpoints of the rod, e.g., ((x1, y1), (x2, y2)).
    :return: The angle in degrees, where 0 is vertical, positive is to the right, and negative is to the left.
    """
    (x1, y1), (x2, y2) = rod_endpoints

    # Identify the pivot point (higher endpoint)
    if y1 < y2:
        x_pivot, y_pivot = x1, y1
        x_end, y_end = x2, y2
    else:
        x_pivot, y_pivot = x2, y2
        x_end, y_end = x1, y1

    # Calculate the difference in coordinates
    dx = x_end - x_pivot
    dy = y_end - y_pivot

    # Calculate the angle using arctan2.
    angle_radians = np.arctan2(dx, dy)
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees
