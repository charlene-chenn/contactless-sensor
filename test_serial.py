import json
import serial
import time

CONFIG_FILE = 'config.json'

def load_serial_config():
    """Loads serial configuration from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        serial_config = config.get('serial', {})
        port = serial_config.get('port')
        baud_rate = serial_config.get('baud_rate', 9600)
        
        if not port:
            print(f"Error: 'port' not found in the 'serial' section of {CONFIG_FILE}")
            return None, None
            
        return port, baud_rate
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Could not parse {CONFIG_FILE}.")
        return None, None

def main():
    """
    Connects to a serial port defined in config.json and prints the output.
    """
    port, baud_rate = load_serial_config()

    if not port:
        return

    print(f"Attempting to connect to serial port '{port}' at {baud_rate} bps...")
    print("Press Ctrl+C to stop.")

    ser = None
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print("Successfully connected. Listening for data...")
        
        while True:
            try:
                line = ser.readline()
                if line:
                    # Decode bytes to a string, removing any leading/trailing whitespace
                    line_str = line.decode('utf-8').strip()
                    print(f"Received: {line_str}")
                
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
            except UnicodeDecodeError:
                print(f"Received non-UTF-8 data: {line}")

    except serial.SerialException as e:
        print(f"Error: Could not open serial port '{port}': {e}")
        print("Please ensure the device is connected and the port in config.json is correct.")
    except KeyboardInterrupt:
        print("\nStopping serial test script.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
