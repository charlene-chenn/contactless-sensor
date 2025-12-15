import argparse
import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy import signal

CONFIG_PATH = "./config.json"
START_IDX = 2700


def rmse(y_true, y_pred):
    """Calculates the Root Mean Square Error between two signals."""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def analyse_frequencies(dataframes: List[pd.DataFrame], labels: List[str]):
    """Calculates and plots the frequency spectrum of the given dataframes."""
    analyses = []
    for data in dataframes:
        N = data.shape[0]
        if N < 2:
            analyses.append([np.array([]), np.array([])])
            continue

        timestamps_s = data["timestamp"].to_numpy() / 1e9
        sample_spacing_s = (timestamps_s[-1] - timestamps_s[0]) / (N - 1)
        measurements = data["measurement"]

        y_freq = 2.0 / N * np.abs(np.fft.fft(measurements)[:N // 2])
        x_freq = np.fft.fftfreq(N, d=sample_spacing_s)[:N // 2]
        analyses.append([x_freq, y_freq])

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, (x_freq, y_freq) in enumerate(analyses):
        ax.plot(x_freq, y_freq, label=labels[i])
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    plt.show()


def load_and_prepare_data(filepath: str) -> (pd.DataFrame, pd.DataFrame):
    """Loads raw data, splits it, and prepares it for calibration."""
    raw_data = pd.read_csv(filepath, parse_dates=["timestamp"])

    vision_sensor_raw = raw_data[raw_data["source"] == "vision_sensor"].astype({"timestamp": "int64"})
    del vision_sensor_raw["source"]

    ground_truth = raw_data[raw_data["source"] == "ground_truth_serial"].astype({"timestamp": "int64"}).iloc[START_IDX:]
    del ground_truth["source"]

    vision_interpolated = np.interp(
        ground_truth["timestamp"],
        vision_sensor_raw["timestamp"],
        vision_sensor_raw["measurement"]
    )
    return vision_interpolated, ground_truth


def calibrate_and_convert_to_windspeed(vision_interpolated: np.ndarray, ground_truth: pd.DataFrame) -> (np.ndarray, float):
    """Converts sensor readings to wind speed and finds the scaling constant k."""
    wind_speed = np.sqrt(np.abs(np.tan(np.deg2rad(vision_interpolated)))).reshape(-1, 1)
    k = float(np.linalg.lstsq(wind_speed, ground_truth["measurement"].to_numpy().reshape(-1, 1), rcond=None)[0][0, 0])
    print(f"Solved for k: {k}")
    return (wind_speed * k).flatten(), k


def optimise_filter_parameters(wind_speed: np.ndarray, ground_truth_measurements: np.ndarray, fs: float) -> Dict[str, Any]:
    """Performs a grid search to find the optimal filter parameters."""
    print("Finding optimal filter parameters...")
    orders = range(2, 7)
    cutoffs = np.arange(0.1, 1.5, 0.05)
    best_params = {"order": 0, "cutoff": 0}
    min_rmse = float('inf')

    for order in orders:
        for cutoff in cutoffs:
            sos = signal.butter(order, cutoff, 'low', fs=fs, output='sos')
            wind_speed_smoothed = signal.sosfilt(sos, wind_speed)
            error = rmse(ground_truth_measurements, wind_speed_smoothed)
            if error < min_rmse:
                min_rmse = error
                best_params = {"order": order, "cutoff": cutoff, "rmse": min_rmse}

    print(f"Optimal parameters found: Order={best_params['order']}, Cutoff={best_params['cutoff']:.2f} Hz (RMSE: {best_params['rmse']:.4f})")
    return best_params


def apply_filter(wind_speed: np.ndarray, fs: float, filter_params: Dict[str, Any]) -> np.ndarray:
    """Applies a Butterworth filter to the wind speed signal."""
    cutoff_hz = filter_params["cutoff_hz"]
    order = filter_params["order"]
    print(f"Using filter: Order={order}, Cutoff={cutoff_hz:.2f} Hz")
    sos = signal.butter(order, cutoff_hz, 'low', fs=fs, output='sos')
    return signal.sosfilt(sos, wind_speed)


def plot_results(ground_truth: pd.DataFrame, wind_speed: np.ndarray, wind_speed_smoothed: np.ndarray):
    """Plots the time-domain and frequency-domain results."""
    vision_sensor_calibrated = pd.DataFrame({"timestamp": ground_truth["timestamp"], "measurement": wind_speed})
    vision_sensor_smoothed = pd.DataFrame({"timestamp": ground_truth["timestamp"], "measurement": wind_speed_smoothed})

    analyse_frequencies([vision_sensor_calibrated, vision_sensor_smoothed, ground_truth], ["Vision", "Vision Smoothed", "GT"])

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(ground_truth.index, ground_truth["measurement"], label="GT")
    ax.plot(ground_truth.index, wind_speed, label="Vision")
    ax.plot(ground_truth.index, wind_speed_smoothed, label="Vision Smoothed")
    ax.set_ylabel("Measurement (m/s)")
    ax.set_xlabel("Sample Number")
    ax.legend()
    plt.show()


def save_results(k_to_save: float, accepted_filter_params: Dict, original_config: Dict, side: str):
    """Handles saving the updated parameters to the config file."""
    should_write_to_file = False
    config_to_write = original_config.copy()

    if input("Save K to config.json? [y/N]: ").lower() == "y":
        config_to_write["conversion_params"][side]["scale_constant"] = k_to_save
        should_write_to_file = True

    if accepted_filter_params:
        if input("Save optimised filter parameters to config.json? [y/N]: ").lower() == "y":
            config_to_write["butterworth_filter"][side] = {
                "cutoff_hz": accepted_filter_params["cutoff"],
                "order": accepted_filter_params["order"]
            }
            should_write_to_file = True

    if should_write_to_file:
        with open(CONFIG_PATH, "w") as json_file:
            json.dump(config_to_write, json_file, indent=4)
        print("config.json saved.")


def main():
    """Main function to run the calibration and analysis process."""

    parser = argparse.ArgumentParser(description="Calibrate the sensor on data.")
    parser.add_argument("--side", type=str, required=True, choices=["left", "right"], help="Chooses which is being calibrated for.")

    args = parser.parse_args()

    calibration_file_path = f"./calibration/{args.side}_tunnel_calibration.csv"

    with open(CONFIG_PATH, "r") as json_file:
        config = json.load(json_file)

    vision_interpolated, ground_truth = load_and_prepare_data(calibration_file_path)
    wind_speed, k = calibrate_and_convert_to_windspeed(vision_interpolated, ground_truth)

    fs = 1 / ((ground_truth["timestamp"].iloc[1] - ground_truth["timestamp"].iloc[0]) / 1e9)
    ground_truth_measurements = ground_truth["measurement"].to_numpy()

    accepted_optimised_params = None
    if input("Run filter parameter optimisation? [y/N]: ").lower() == "y":
        best_params = optimise_filter_parameters(wind_speed, ground_truth_measurements, fs)
        if input("Use these parameters for this session? [y/N]: ").lower() == "y":
            config["butterworth_filter"]["order"] = best_params["order"]
            config["butterworth_filter"]["cutoff_hz"] = best_params["cutoff"]
            accepted_optimised_params = best_params

    wind_speed_smoothed = apply_filter(wind_speed, fs, config["butterworth_filter"])

    plot_results(ground_truth, wind_speed, wind_speed_smoothed)

    save_results(k, accepted_optimised_params, config, args.side)


if __name__ == "__main__":
    main()
