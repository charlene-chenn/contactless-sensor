import cv2

class Camera:
    """
    A class to handle camera operations.
    """

    def __init__(self, camera_index: int):
        """
        Initializes the camera.

        :param camera_index: The index of the camera to use.
        """
        self.camera_index = camera_index
        self.cap = None

    def initialize(self):
        """
        Initializes the camera capture.

        :return: True if the camera was successfully initialized, False otherwise.
        """
        self.cap = cv2.VideoCapture(self.camera_index)
        return self.cap.isOpened()

    def read_frame(self):
        """
        Reads a frame from the camera.

        :return: A tuple containing a boolean and the frame. The boolean is True if the frame was successfully read, False otherwise.
        """
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        """
        Releases the camera.
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None
