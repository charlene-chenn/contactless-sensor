# Contactless Sensor System

A computer vision-based contactless sensor system for measuring angles and wind speeds using color-based object detection. Developed for COMP0219.

## Overview

This system uses a camera to track colored objects (balls or rods) and calculate their angular displacement relative to a vertical reference. It can operate in two modes:
- **Two Balls Mode**: Tracks a pivot ball and a moving ball to calculate the angle between them
- **Rod and Ball Mode**: Tracks a colored rod and calculates its angle relative to vertical

The system can interface with Arduino sensors via serial communication for ground truth measurements and data logging.

## Features

- Real-time angle measurement using computer vision
- Two detection modes: two-ball tracking or rod tracking
- HSV color-based object detection with customizable color ranges
- Interactive calibration utility for color tuning
- Serial communication support for external sensors
- Data logging with synchronized angle and wind speed measurements
- Headless operation mode for automated data collection
- Camera selection and configuration management

## Project Structure

```
contactless-sensor/
├── src/
│   ├── main.py           # Main application entry point
│   ├── detection.py      # Ball and rod detection algorithms
│   ├── calculation.py    # Angle calculation functions
│   ├── camera.py         # Camera interface and management
│   └── ui.py            # User interface and visualization
├── tests/
│   ├── test_detection.py
│   └── test_calculation.py
├── camera_calibration/   # Camera calibration utilities
├── config.json          # Configuration file (colors, camera, serial)
├── calibrate.py         # Color calibration utility
├── datalogger.py        # Data logging script
├── test_serial.py       # Serial connection testing
└── requirements.txt     # Python dependencies
```

## Installation

### Prerequisites

- Python 3.7 or higher
- Webcam or camera module
- (Optional) Arduino or compatible device for serial communication

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd contactless-sensor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** `picamera2` is only required for Raspberry Pi. For other systems, it will be skipped automatically.

## Usage

### Basic Operation

Run the main application with default settings:
```bash
python -m src.main
```

### Command Line Options

- `--output-angle`: Output raw angle values to console (useful for scripting)
- `--no-ui`: Run without graphical interface (headless mode)

Example:
```bash
python -m src.main --output-angle --no-ui
```

### Color Calibration

Before first use, calibrate the color detection:

1. Run the calibration tool:
```bash
python calibrate.py
```

2. Click on the object you want to track (pivot ball, moving ball, or rod)
3. Adjust the HSV range trackbars to fine-tune the mask
4. Press the appropriate key to save:
   - `s` - Save pivot ball color
   - `m` - Save moving ball color
   - `r` - Save rod color
5. Press `q` to quit

The calibrated colors are automatically saved to `config.json`.

### Data Logging

Log synchronized angle and wind speed data:

```bash
python datalogger.py --output-file sensor_log.csv
```

This will:
1. Start the angle measurement in headless mode
2. Connect to the serial port for wind speed readings
3. Log synchronized data to a CSV file
4. Continue until stopped with Ctrl+C

### Configuration

Edit `config.json` to customize:

```json
{
    "camera_index": 0,           // Camera device index
    "mode": "two_balls",         // "two_balls" or "rod_and_ball"
    "ball_colors": {
        "pivot": {
            "lower": [8, 192, 176],
            "upper": [28, 255, 255]
        },
        "moving": {
            "lower": [44, 111, 145],
            "upper": [64, 211, 245]
        }
    },
    "rod_color": {
        "lower": [139, 163, 179],
        "upper": [159, 255, 255]
    },
    "serial": {
        "port": "/dev/tty.usbmodem14201",
        "baud_rate": 9600
    }
}
```

## Detection Modes

### Two Balls Mode (`two_balls`)

Tracks two colored balls:
- **Pivot Ball**: Fixed reference point
- **Moving Ball**: Tracked for angle calculation

The angle is calculated from the pivot ball to the moving ball, with 0° being vertical (straight down), positive angles to the right, and negative angles to the left.

### Rod and Ball Mode (`rod_and_ball`)

Tracks a colored rod using Hough Line Transform. The angle is calculated from the rod's orientation relative to vertical.

## Angle Calculation

Angles are measured from vertical (downward):
- **0°**: Straight down (vertical)
- **Positive**: Clockwise from vertical (to the right)
- **Negative**: Counter-clockwise from vertical (to the left)
- **Range**: -180° to +180°

## Serial Communication

The system supports serial communication for external sensors (e.g., anemometers):
- Default baud rate: 9600
- Expected format: Float values or `ID,value` pairs
- Configuration: Set port and baud rate in `config.json`

Test serial connection:
```bash
python test_serial.py
```

## Testing

Run unit tests:
```bash
python -m pytest tests/
```

## Troubleshooting

### Camera Not Found
- Check `camera_index` in `config.json`
- Run the main program to auto-select available camera
- Ensure camera permissions are granted

### Poor Detection
- Use `calibrate.py` to recalibrate colors
- Ensure good lighting conditions
- Adjust HSV ranges for better color matching
- Check that tracked objects are visible and unobstructed

### Serial Connection Issues
- Verify correct port in `config.json` (use `ls /dev/tty.*` on macOS/Linux)
- Check that device is connected and drivers are installed
- Ensure no other program is using the serial port

## Dependencies

- **opencv-python**: Computer vision and image processing
- **numpy**: Numerical computations
- **pyserial**: Serial communication
- **picamera2**: Raspberry Pi camera support (optional)

## Development

### Camera Calibration

For improved accuracy with distortion correction, see the `camera_calibration/` directory for intrinsic camera calibration utilities.

### Adding New Detection Methods

Implement new detection algorithms in `src/detection.py` and corresponding angle calculations in `src/calculation.py`.

## License

This project was developed for COMP0219.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style conventions
- Tests pass before submitting
- New features include appropriate documentation

## Authors

Developed as part of COMP0219 coursework.
