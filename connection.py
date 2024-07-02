# connection.py
import cv2
from PyQt5.QtCore import QTimer
from video import ClickableLabel, update_video_stream

def setup_video_stream(app,vid):
    app.video_label = ClickableLabel()
    app.video_label.clicked.connect(app.handle_video_click)
    app.cap = cv2.VideoCapture(vid)
    app.timer = QTimer()
    app.timer.timeout.connect(lambda: update_video_stream(app))
    app.timer.start(30)
    return app.video_label
