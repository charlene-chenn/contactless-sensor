import argparse
import collections
import csv
import json
import queue
import subprocess
import threading
import time
from datetime import datetime

import matplotlib.pyplot as plt
import serial

# --- Configuration ---
CONFIG_FILE = 'config.json'
# New, more flexible field names
FIELDNAMES = ['timestamp', 'source', 'measurement']


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
    is_serial = isinstance(stream, serial.Serial)

    # Use iter(stream.readline, '') for text streams from subprocess
    # Use a manual while loop for byte streams from serial
    iterator = iter(stream.readline, '') if not is_serial else iter(lambda: True, False)

    for line in iterator:
        try:
            if is_serial:
                line_bytes = stream.readline()
                if not line_bytes:
                    if stream.closed or not stream.is_open:
                        break
                    continue
                line_str = line_bytes.decode(errors='ignore').strip()
            else:
                line_str = line.strip()

            if line_str:
                try:
                    parts = line_str.split(',')
                    value_str = parts[-1]
                    value = float(value_str)
                    queue_obj.put(value)
                except (ValueError, IndexError):
                    # print(f"Warning: Could not parse value from {stream_type}: {line_str}")
                    continue
        except Exception as e:
            if not (is_serial and not stream.is_open):
                print(f"Error reading from {stream_type}: {e}")
            break
    print(f"{stream_type} stream finished.")


def print_stream_errors(stream, stream_name):
    """Reads lines from a text stream and prints them as errors."""
    for line in iter(stream.readline, ''):
        print(f"[{stream_name} ERROR] {line.strip()}")
    stream.close()


def main():
    """
    Main function to run the data logger.
    """
    parser = argparse.ArgumentParser(description='Log data from a vision sensor and a serial device.')
    parser.add_argument('--output-file', type=str, default='sensor_log.csv',
                        help='Name of the CSV file to save logs to (default: sensor_log.csv)')
    parser.add_argument('--vision-debug', action='store_true',
                        help='Enable the UI for the vision process for debugging purposes.')
    parser.add_argument('--plot', action='store_true',
                        help='Enable a live plot of the sensor data.')
    args = parser.parse_args()

    OUTPUT_CSV_FILE = args.output_file

    serial_port, baud_rate = load_config()

    vision_process = None
    ser = None

    # --- Plotting setup ---
    if args.plot:
        plt.ion()
        fig, ax = plt.subplots()
        ax.set_ylim(0, 10)
        vision_data = collections.deque(maxlen=500)
        serial_data = collections.deque(maxlen=500)
        vision_line, = ax.plot([], [], 'r-', label='Vision Sensor')
        serial_line, = ax.plot([], [], 'bo-', markersize=3, label='Ground Truth (Serial)')
        ax.legend()
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Measurement')
        ax.set_title('Live Sensor Data')
        start_time = time.time()

    try:
        # Start the vision measurement script as a subprocess
        # Use python's -u flag for unbuffered output, which is crucial for pipes
        base_cmd = ["python3", "-u", "-m", "src.main", "--output", "windspeed"]
        if args.vision_debug:
            print("Starting vision sensor process in DEBUG mode (UI enabled)...")
            vision_process_cmd = base_cmd
        else:
            print("Starting headless vision sensor process...")
            vision_process_cmd = base_cmd + ["--no-ui"]

        vision_process = subprocess.Popen(
            vision_process_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Open streams in text mode, handles decoding
            bufsize=1   # Use line-buffering
        )

        time.sleep(3)
        print("Vision sensor process started.")

        # Set up serial connection for the ground truth sensor
        print(f"Connecting to serial port {serial_port} at {baud_rate} bps...")
        try:
            ser = serial.Serial(serial_port, baud_rate, timeout=1)
            print("Serial port connected.")
        except serial.SerialException as e:
            print(f"Error: Could not open serial port {serial_port}: {e}")
            if args.plot:
                plt.close(fig)
            return

        # Queues to hold data from the threads
        vision_queue = queue.Queue()
        serial_queue = queue.Queue()

        # Start threads to read from subprocess stdout, stderr and serial port
        vision_thread = threading.Thread(
            target=read_stream_to_queue,
            args=(vision_process.stdout, vision_queue, 'vision_sensor'),
            daemon=True
        )
        serial_thread = threading.Thread(
            target=read_stream_to_queue,
            args=(ser, serial_queue, 'ground_truth_serial'),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=print_stream_errors,
            args=(vision_process.stderr, 'vision_sensor'),
            daemon=True
        )
        vision_thread.start()
        serial_thread.start()
        stderr_thread.start()

        with open(OUTPUT_CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            print(f"Logging data to {OUTPUT_CSV_FILE}. Press Ctrl+C to stop.")

            last_plot_time = time.time()
            new_data_received = False

            while True:
                # Check for new vision sensor data
                try:
                    measurement = vision_queue.get_nowait()
                    timestamp = time.time()
                    writer.writerow({
                        'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                        'source': 'vision_sensor',
                        'measurement': f"{measurement:.4f}"
                    })
                    if args.plot:
                        vision_data.append((timestamp, measurement))
                        new_data_received = True
                except queue.Empty:
                    pass

                # Check for new serial data
                try:
                    measurement = serial_queue.get_nowait()
                    timestamp = time.time()
                    writer.writerow({
                        'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                        'source': 'ground_truth_serial',
                        'measurement': f"{measurement:.4f}"
                    })
                    if args.plot:
                        serial_data.append((timestamp, measurement))
                        new_data_received = True
                except queue.Empty:
                    pass

                # Update the plot periodically
                now = time.time()
                if args.plot and new_data_received and (now - last_plot_time > 0.2): # 200ms throttle
                    last_plot_time = now
                    new_data_received = False

                    vision_x, vision_y, serial_x, serial_y = [], [], [], []
                    
                    try:
                        vision_x_ts, vision_y_data = zip(*vision_data)
                        vision_x = [t - start_time for t in vision_x_ts]
                        vision_y = list(vision_y_data)
                    except ValueError:
                        pass # Deque is empty

                    try:
                        serial_x_ts, serial_y_data = zip(*serial_data)
                        serial_x = [t - start_time for t in serial_x_ts]
                        serial_y = list(serial_y_data)
                    except ValueError:
                        pass # Deque is empty

                    vision_line.set_data(vision_x, vision_y)
                    serial_line.set_data(serial_x, serial_y)

                    ax.relim()
                    ax.autoscale_view()
                    fig.canvas.draw()
                    fig.canvas.flush_events()

                if vision_process.poll() is not None:
                    print("Vision sensor process has terminated.")
                    time.sleep(0.1)
                    break

                time.sleep(0.001)  # Small sleep to prevent busy-waiting

    except KeyboardInterrupt:
        print("\nStopping data logger...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if args.plot:
            plt.close(fig)
        if vision_process:
            print("Terminating vision sensor process.")
            vision_process.terminate()
            vision_process.wait()
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        print("Data logging finished.")


if __name__ == "__main__":
    main()
