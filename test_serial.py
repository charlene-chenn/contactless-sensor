import json
import serial
import time

CONFIG_FILE = 'config.json'

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

def main():
    """
    Connects to the serial port and prints all incoming data.
    """
    serial_port, baud_rate = load_config()
    ser = None

    print(f"Attempting to connect to serial port {serial_port} at {baud_rate} bps...")

    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        print("Serial port connected. Waiting for data...")

        while True:
            try:
                line = ser.readline()
                if line:
                    try:
                        line_str = line.decode('utf-8').strip()
                        print(line_str)
                    except UnicodeDecodeError:
                        print(f"Received non-UTF8 bytes: {line}")
                
                # A small sleep to be kind to the CPU
                time.sleep(0.01)

            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
            except KeyboardInterrupt:
                print("\nStopping serial monitor...")
                break

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {serial_port}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
