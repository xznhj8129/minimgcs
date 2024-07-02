# video.py
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from shared_data import shared_data
import cv2

class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)  # Signal to emit coordinates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setScaledContents(False)
        self.setMinimumSize(640, 480)
        self.original_size = (640, 480)  # Initialize with default original size

    def setOriginalSize(self, width, height):
        self.original_size = (width, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            y = event.pos().y()
            video_aspect_ratio = self.original_size[0] / self.original_size[1]
            label_aspect_ratio = self.width() / self.height()
            if label_aspect_ratio > video_aspect_ratio:
                scaled_height = self.height()
                scaled_width = int(video_aspect_ratio * scaled_height)
            else:
                scaled_width = self.width()
                scaled_height = int(scaled_width / video_aspect_ratio)
            offset_x = (self.width() - scaled_width) // 2
            offset_y = (self.height() - scaled_height) // 2
            if offset_x <= x <= offset_x + scaled_width and offset_y <= y <= offset_y + scaled_height:
                scaled_x = (x - offset_x) * self.original_size[0] / scaled_width
                scaled_y = (y - offset_y) * self.original_size[1] / scaled_height
                shared_data.video_click_x = int(scaled_x)
                shared_data.video_click_y = int(scaled_y)
                shared_data.video_select = True
                #print(f"V Clicked coordinates in original frame: ({scaled_x}, {scaled_y})")  # Debug print
                self.clicked.emit(int(scaled_x), int(scaled_y))
            else:
                pass#print("Clicked outside of video frame")


def update_video_stream(app):
    ret, frame = app.cap.read()
    if ret:
        app.video_label.setOriginalSize(frame.shape[1], frame.shape[0])  # Update original size
        app.video_label.ratio = app.video_label.original_size[0] / app.video_label.original_size[1]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if shared_data.video_select:
            x, y = shared_data.video_click_x, shared_data.video_click_y
            frame = cv2.rectangle(frame, (x-25, y-25), (x+25, y+25), (0, 255, 0), 2)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        app.video_label.setPixmap(QPixmap.fromImage(q_img.scaled(app.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)))
    else:
        app.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart the video

