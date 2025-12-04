import argparse
import os
import shutil
import subprocess
import time
from datetime import datetime


def main():
    """
    Main function to run the calibration script.
    """
    parser = argparse.ArgumentParser(description="Automated calibration script for the contactless sensor.")
    parser.add_argument("--side", type=str, required=True, choices=["left", "right"], help="The tunnel side to calibrate.")
    args = parser.parse_args()

    # --- Configuration ---
    datalogger_output_file = "datalogger.csv"
    calibration_duration = 40
    calibration_dir = "calibration"
    archive_dir = os.path.join(calibration_dir, f"old_{args.side}")
    calibration_file = os.path.join(calibration_dir, f"{args.side}_tunnel_calibration.csv")

    # --- 1. Run Datalogger ---
    print(f"Starting datalogger for {args.side} tunnel for {calibration_duration} seconds...")
    datalogger_cmd = [
        "python3",
        "datalogger.py",
        "--side",
        args.side,
        "--vision-output",
        "angle",
        "--output-file",
        datalogger_output_file,
    ]

    # Start the datalogger process
    process = subprocess.Popen(datalogger_cmd)

    # Wait for the specified duration
    try:
        process.wait(timeout=calibration_duration)
    except subprocess.TimeoutExpired:
        print("Calibration duration finished. Terminating datalogger...")
        process.terminate()
        process.wait()

    print("Datalogger finished.")

    # --- 2. Archive and Replace Calibration File ---
    if os.path.exists(datalogger_output_file):
        # Only archive the old file if a new one was successfully created.
        if os.path.exists(calibration_file):
            print(f"Archiving old calibration file: {calibration_file}")
            # Create archive directory if it doesn't exist
            os.makedirs(archive_dir, exist_ok=True)

            # Create timestamp for the archived file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file_name = f"{timestamp}_{args.side}_tunnel_calibration.csv"
            archive_path = os.path.join(archive_dir, archive_file_name)

            # Move the old calibration file
            shutil.move(calibration_file, archive_path)
            print(f"Old calibration file moved to: {archive_path}")

        # Move the new calibration file into place.
        print(f"Moving new calibration data to: {calibration_file}")
        shutil.move(datalogger_output_file, calibration_file)
    else:
        print(f"Warning: Datalogger did not produce the output file: {datalogger_output_file}")
        print("The existing calibration file has been left unchanged.")

if __name__ == "__main__":
    main()
