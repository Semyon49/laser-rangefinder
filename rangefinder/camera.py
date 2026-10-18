"""Источники кадров: OpenCV (USB/Windows) и Picamera2 (CSI-камера на Raspberry Pi)."""
import platform
import sys

import cv2


class OpenCVCamera:
    def __init__(self, index=0, width=1280, height=720, exposure=None):
        self.cap = (cv2.VideoCapture(index, cv2.CAP_DSHOW)
                    if platform.system() == "Windows" else cv2.VideoCapture(index))
        if not self.cap.isOpened():
            sys.exit("Камера не открылась")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if exposure is not None:                 # значение зависит от драйвера; best effort
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

    def read(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def close(self):
        self.cap.release()


class PiCamera:
    def __init__(self, width=1280, height=720, exposure=None, gain=1.0):
        try:
            from picamera2 import Picamera2
        except ImportError:
            sys.exit("Нет picamera2: sudo apt install python3-picamera2")
        self.cam = Picamera2()
        # В picamera2 формат "RGB888" отдаёт массив с порядком каналов BGR, как нужно OpenCV
        cfg = self.cam.create_video_configuration(main={"size": (width, height), "format": "RGB888"})
        self.cam.configure(cfg)
        if exposure is not None:                 # exposure в микросекундах
            self.cam.set_controls({"AeEnable": False, "ExposureTime": int(exposure),
                                   "AnalogueGain": float(gain), "AwbEnable": False})
        self.cam.start()

    def read(self):
        return self.cam.capture_array()

    def close(self):
        self.cam.stop()


def open_camera(kind, index=0, width=1280, height=720, exposure=None, gain=1.0):
    if kind == "auto":
        try:
            import picamera2  # noqa: F401
            kind = "picamera2"
        except ImportError:
            kind = "opencv"
    if kind == "picamera2":
        return PiCamera(width, height, exposure, gain)
    return OpenCVCamera(index, width, height, exposure)
