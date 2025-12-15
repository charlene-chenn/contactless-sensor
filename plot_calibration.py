
import json

import matplotlib.pyplot as plt
import numpy as np


def wind_speed_formula(angle_deg, scale_constant):
    """Calculates wind speed from angle using the project's formula."""
    angle_rad = np.deg2rad(angle_deg)
    return scale_constant * np.sqrt(np.abs(np.tan(angle_rad)))


def plot_calibration_curves():
    """
    Loads calibration constants from config.json and plots the wind speed
    curves for the left and right tunnels.
    """
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Make sure the file is in the same directory.")
        return

    left_params = config.get('conversion_params', {}).get('left', {})
    right_params = config.get('conversion_params', {}).get('right', {})

    if not left_params or not right_params:
        print("Error: Could not find 'conversion_params' for 'left' and 'right' in config.json.")
        return

    k_left = left_params.get('scale_constant')
    k_right = right_params.get('scale_constant')

    if k_left is None or k_right is None:
        print("Error: 'scale_constant' not found for left or right tunnel in config.json.")
        return

    # Generate a range of angles, avoiding the asymptote at 90 degrees
    angles = np.linspace(0, 40, 400)

    # Calculate wind speed for both tunnels
    speed_left = wind_speed_formula(angles, k_left)
    speed_right = wind_speed_formula(angles, k_right)

    # Create the plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(angles, speed_left, label=f'Left Tunnel (k={k_left:.2f})', color='blue')
    ax.plot(angles, speed_right, label=f'Right Tunnel (k={k_right:.2f})', color='red')

    # Formatting
    ax.set_title('Wind Speed Calibration Curves', fontsize=16)
    ax.set_xlabel('Angle (degrees)', fontsize=12)
    ax.set_ylabel('Wind Speed (m/s)', fontsize=12)
    ax.legend(fontsize=10)
    ax.set_xlim(0, 40)
    ax.set_ylim(0, max(np.max(speed_left), np.max(speed_right)) * 1.1)  # Adjust y-limit for better visuals
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Save the figure
    plt.savefig('./Figures/calibration_curves.png', dpi=300, bbox_inches='tight')

    print("Successfully generated and saved 'calibration_curves.png'")


if __name__ == '__main__':
    plot_calibration_curves()
