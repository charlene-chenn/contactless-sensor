import cv2
import platform
import time

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

class Camera:
    """
    A class to handle camera operations for both standard USB cameras and Raspberry Pi cameras.
    """

    def __init__(self, camera_index: int):
        """
        Initializes the camera.

        :param camera_index: The index of the camera to use.
        """
        self.camera_index = camera_index
        self.is_rpi = platform.machine().startswith('arm') or platform.machine().startswith('aarch64')
        
        if self.is_rpi and Picamera2:
            self.picam2 = Picamera2()
        else:
            self.cap = None

    def initialize(self):
        """
        Initializes the camera capture.

        :return: True if the camera was successfully initialized, False otherwise.
        """
        if self.is_rpi and Picamera2:
            try:
                config = self.picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
                self.picam2.configure(config)
                self.picam2.start()
                time.sleep(0.3) # Warm-up for AE/AWB
                return True
            except Exception as e:
                print(f"Failed to initialize Raspberry Pi camera: {e}")
                return False
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
            return self.cap.isOpened()

    def read_frame(self):
        """
        Reads a frame from the camera.

        :return: A tuple containing a boolean and the frame. The boolean is True if the frame was successfully read, False otherwise.
        """
        if self.is_rpi and Picamera2:
            if self.picam2.is_started: # Check if camera is started
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Convert RGB to BGR for OpenCV
                return True, frame
            else:
                return False, None
        else:
            if self.cap is None:
                return False, None
            return self.cap.read()

    def release(self):
        """
        Releases the camera.
        """
        if self.is_rpi and Picamera2:
            if self.picam2.is_started: # Check if camera is started
                self.picam2.stop()
        else:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
