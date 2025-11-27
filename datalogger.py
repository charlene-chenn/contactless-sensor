import csv
import json
import subprocess
import serial
import time
from datetime import datetime
import threading
import queue
import argparse

# --- Configuration ---
CONFIG_FILE = 'config.json'
FIELDNAMES = ['timestamp', 'angle', 'wind_speed_ms']

def load_config():
    """Loads serial configuration from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        serial_config = config.get('serial', {})
        port = serial_config.get('port', '/dev/tty.usbmodem14201')
        baud_rate = serial_config.get('baud_rate', 9600)
        return port, baud_rate
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found. Using default serial settings.")
        return '/dev/tty.usbmodem14201', 9600

def read_stream_to_queue(stream, queue_obj, stream_type):
    """
    Reads lines from a stream (subprocess stdout or serial)
    and puts them into a queue.
    """
    while not stream.closed:
        try:
            line = stream.readline()
            if not line:
                break
            # For subprocess, output is bytes, so decode it
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            
            line = line.strip()
            if line:
                queue_obj.put(line)
        except Exception as e:
            print(f"Error reading from {stream_type}: {e}")
            break
    print(f"{stream_type} stream finished.")

def main():
    """
    Main function to run the data logger.
    """
    parser = argparse.ArgumentParser(description='Log data from contactless sensor and serial ground truth.')
    parser.add_argument('--output-file', type=str, default='sensor_log.csv',
                        help='Name of the CSV file to save logs to (default: sensor_log.csv)')
    args = parser.parse_args()

    OUTPUT_CSV_FILE = args.output_file

    serial_port, baud_rate = load_config()

    angle_process = None
    ser = None

    try:
        # Start the angle measurement script as a subprocess, with no UI
        print("Starting headless angle measurement process...")
        angle_process_cmd = ["python3", "-m", "src.main", "--output-angle", "--no-ui"]
        angle_process = subprocess.Popen(
            angle_process_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # Work with bytes
        )

        # Give the camera process a moment to initialize
        time.sleep(3)
        print("Angle measurement process started.")

        # Set up serial connection for the ground truth sensor
        print(f"Connecting to serial port {serial_port} at {baud_rate} bps...")
        try:
            ser = serial.Serial(serial_port, baud_rate, timeout=1)
            print("Serial port connected.")
        except serial.SerialException as e:
            print(f"Error: Could not open serial port {serial_port}: {e}")
            print("Please check the port name in config.json and ensure the device is connected.")
            return

        # Queues to hold data from the threads
        angle_queue = queue.Queue()
        serial_queue = queue.Queue()

        # Start threads to read from subprocess and serial port
        angle_thread = threading.Thread(
            target=read_stream_to_queue,
            args=(angle_process.stdout, angle_queue, 'angle_process'),
            daemon=True
        )
        serial_thread = threading.Thread(
            target=read_stream_to_queue,
            args=(ser, serial_queue, 'serial'),
            daemon=True
        )
        angle_thread.start()
        serial_thread.start()

        # Open CSV file for writing
        with open(OUTPUT_CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            print(f"Logging data to {OUTPUT_CSV_FILE}. Press Ctrl+C to stop.")

            last_angle = None
            last_wind_speed = None

            while True:
                # Get the latest data from queues, but don't block
                try:
                    angle_line = angle_queue.get_nowait()
                    try:
                        last_angle = float(angle_line)
                    except ValueError:
                        print(f"Could not parse angle value: {angle_line}")
                except queue.Empty:
                    pass # No new angle data, use the last one

                try:
                    serial_line = serial_queue.get_nowait()
                    try:
                        last_wind_speed = float(serial_line)
                    except ValueError:
                         print(f"Could not parse wind speed value: {serial_line}")
                except queue.Empty:
                    pass # No new serial data, use the last one

                # Write a row if we have at least one value for each
                if last_angle is not None and last_wind_speed is not None:
                    writer.writerow({
                        'timestamp': datetime.now().isoformat(),
                        'angle': f"{last_angle:.2f}",
                        'wind_speed_ms': f"{last_wind_speed:.2f}"
                    })
                    print(f"Logged: Angle={last_angle:.2f}, Wind Speed={last_wind_speed:.2f}")
                    # Reset them to require new readings for the next row
                    last_angle = None
                    last_wind_speed = None

                # Check if the subprocess has terminated
                if angle_process.poll() is not None:
                    print("Angle measurement process has terminated.")
                    break
                
                # Small delay to prevent a busy loop
                time.sleep(0.1)


    except KeyboardInterrupt:
        print("\nStopping data logger...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if angle_process:
            print("Terminating angle measurement process.")
            angle_process.terminate()
            angle_process.wait()
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        print("Data logging finished.")

if __name__ == "__main__":
    main()

