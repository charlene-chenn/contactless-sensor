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
                config = self.picam2.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)})
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
            if self.picam2.started: # Check if camera is started
                frame = self.picam2.capture_array()
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
            if self.picam2.started: # Check if camera is started
                self.picam2.stop()
        else:
            if self.cap is not None:
                self.cap.release()
                self.cap = None

    @staticmethod
    def get_available_cameras():
        """
        Gets a list of available camera devices.
        :return: A list of available camera indices.
        """
        available_cameras = []
        index = 0
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                break
            available_cameras.append(index)
            cap.release()
            index += 1
        return available_cameras

    @staticmethod
    def select_camera(config: dict):
        """
        Prompts the user to select a camera and updates the config.

        :param config: The configuration dictionary.
        :return: The selected camera index.
        """
        available_cameras = Camera.get_available_cameras()
        if not available_cameras:
            print("Error: No cameras found.")
            return None

        print("Available cameras:", available_cameras)
        camera_index_str = input(f"Select a camera index to use (default: {config.get('camera_index', 0)}): ")
        if camera_index_str.strip() == "":
            camera_index = config.get('camera_index', 0)
        else:
            try:
                camera_index = int(camera_index_str)
                if camera_index not in available_cameras:
                    print("Invalid camera index. Using default.")
                    camera_index = config.get('camera_index', 0)
            except ValueError:
                print("Invalid input. Using default camera index.")
                camera_index = config.get('camera_index', 0)
        
        config['camera_index'] = camera_index
        return camera_index
