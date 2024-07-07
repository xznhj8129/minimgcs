# video.py
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from shared_data import shared_data
import cv2
import numpy as np

def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation = inter)
    return resized, dim

def crop_center(image, crop_width, crop_height):
    if image is None:
        raise ValueError("Image not found or unable to load.")
    height, width = image.shape[:2]
    center_x, center_y = width // 2, height // 2
    x1 = max(0, center_x - crop_width // 2)
    y1 = max(0, center_y - crop_height // 2)
    x2 = min(width, center_x + crop_width // 2)
    y2 = min(height, center_y + crop_height // 2)
    cropped_image = image[y1:y2, x1:x2]
    
    return cropped_image

def setup_video_stream(app, vid):
    app.video_label = ClickableLabel()
    app.video_label.clicked.connect(app.handle_video_click)
    app.video_label.zoom_changed.connect(app.handle_zoom_change)
    app.cap = cv2.VideoCapture(vid)
    app.timer = QTimer()
    app.timer.timeout.connect(lambda: update_video_stream(app))
    app.timer.start(30)
    app.zoom_factor = 1.5
    app.tracker_initialized = False
    return app.video_label

class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)  # Signal to emit coordinates
    zoom_changed = pyqtSignal(float)  # Signal to notify zoom level change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setScaledContents(False)
        self.setMinimumSize(640, 480)
        self.original_size = (640, 480)  # Initialize with default original size
        self.zoom_factor = 1.5

    def setOriginalSize(self, width, height):
        self.original_size = (width, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            y = event.pos().y()

            # Calculate offsets and scaled dimensions from shared data
            offset_x = shared_data.video_offset_x
            offset_y = shared_data.video_offset_y
            scaled_width = shared_data.video_scaled_width
            scaled_height = shared_data.video_scaled_height

            # Normalize the click coordinates
            if offset_x <= x <= offset_x + scaled_width and offset_y <= y <= offset_y + scaled_height:
                normalized_x = (x - offset_x) / scaled_width
                normalized_y = (y - offset_y) / scaled_height

                if shared_data.video_track_zoom_active:
                    x1 = shared_data.video_track_x1
                    y1 = shared_data.video_track_y1
                    zoom_w = shared_data.video_zoom_w
                    zoom_h = shared_data.video_zoom_h
                    scaled_x = normalized_x * zoom_w + x1
                    scaled_y = normalized_y * zoom_h + y1
                else:
                    scaled_x = normalized_x * self.original_size[0]
                    scaled_y = normalized_y * self.original_size[1]

                shared_data.video_click_x = int(scaled_x)
                shared_data.video_click_y = int(scaled_y)
                shared_data.video_track_x = int(scaled_x)
                shared_data.video_track_y = int(scaled_y)
                shared_data.video_select = True
                self.clicked.emit(int(scaled_x), int(scaled_y))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_change = round(0.1 * (delta / 120),1)
        new_zoom = round(shared_data.video_track_zoom_level + zoom_change,1)
        shared_data.video_track_zoom_level = max(1.5, new_zoom)
        self.zoom_factor = shared_data.video_track_zoom_level
        self.zoom_changed.emit(self.zoom_factor)
        print(self.zoom_factor)
        event.accept()


def update_video_stream(app):
    ret, frame = app.cap.read()
    if ret:
        original_height, original_width = frame.shape[:2]
        app.video_label.setOriginalSize(original_width, original_height)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        label_aspect_ratio = app.video_label.width() / app.video_label.height()
        video_aspect_ratio = original_width / original_height

        if label_aspect_ratio > video_aspect_ratio:
            scaled_height = app.video_label.height()
            scaled_width = int(video_aspect_ratio * scaled_height)
        else:
            scaled_width = app.video_label.width()
            scaled_height = int(scaled_width / video_aspect_ratio)

        offset_x = (app.video_label.width() - scaled_width) // 2
        offset_y = (app.video_label.height() - scaled_height) // 2

        if shared_data.video_track_zoom_active:
            if not app.tracker_initialized:
                app.prev_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                app.lk_params = dict(winSize=(15, 15), maxLevel=2,
                                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
                app.tracker_initialized = True

            p0 = np.array([[shared_data.video_track_x, shared_data.video_track_y]], dtype=np.float32)
            current_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            p1, st, err = cv2.calcOpticalFlowPyrLK(app.prev_gray, current_gray, p0, None, **app.lk_params)
            shared_data.video_track_x, shared_data.video_track_y = p1[0][0], p1[0][1]

            app.prev_gray = current_gray
            
            zoom_level = max(1.5, shared_data.video_track_zoom_level)
            x, y = shared_data.video_track_x, shared_data.video_track_y
            zoom_w, zoom_h = int(app.video_label.width() / zoom_level), int(app.video_label.height() / zoom_level)
            x1, y1 = max(0, int(x - zoom_w // 2)), max(0, int(y - zoom_h // 2))
            x2, y2 = min(original_width, int(x + zoom_w // 2)), min(original_height, int(y + zoom_h // 2))
            if (x2 - x1) < zoom_w:
                if x < (label_width / 2):
                    x2 += zoom_w - (x2 - x1)
                else:
                    x1 -= zoom_w - (x2 - x1)

            if (y2 - y1) < zoom_h:
                if y < (label_height / 2):
                    y2 += zoom_h - (y2 - y1)
                else:
                    y1 -= zoom_h - (y2 - y1)

            cropped_frame = frame[y1:y2, x1:x2]
            cropped_frame_h, cropped_frame_w = cropped_frame.shape[:2]

            if cropped_frame_h > cropped_frame_w:
                resized_frame, dim = image_resize(cropped_frame, height=app.video_label.height())
            else:
                resized_frame, dim = image_resize(cropped_frame, width=app.video_label.width())
            frame = crop_center(resized_frame, app.video_label.width(), app.video_label.height())
            resized_height, resized_width = frame.shape[:2]

            pad_y1 = (app.video_label.height() - resized_height) // 2
            pad_y2 = pad_y1 + resized_height
            pad_x1 = (app.video_label.width() - resized_width) // 2
            pad_x2 = pad_x1 + resized_width

            # Normalize tracker coordinates
            tracker_x = (shared_data.video_track_x - x1) * resized_width / zoom_w + pad_x1
            tracker_y = (shared_data.video_track_y - y1) * resized_height / zoom_h + pad_y1
            cv2.rectangle(frame, (int(tracker_x) - 50, int(tracker_y) - 50), (int(tracker_x) + 50, int(tracker_y) + 50), (255, 255, 255), 1)

            # Normalize user click coordinates
            user_click_x = (shared_data.video_click_x - x1) * resized_width / zoom_w + pad_x1
            user_click_y = (shared_data.video_click_y - y1) * resized_height / zoom_h + pad_y1
            cv2.drawMarker(frame, (int(user_click_x), int(user_click_y)), (255, 255, 255), markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)

            # Update shared_data with crop and zoom details
            shared_data.video_track_x1 = x1
            shared_data.video_track_y1 = y1
            shared_data.video_zoom_w = zoom_w
            shared_data.video_zoom_h = zoom_h
            shared_data.video_scaled_width = resized_width
            shared_data.video_scaled_height = resized_height
            shared_data.video_offset_x = pad_x1
            shared_data.video_offset_y = pad_y1

        else:
            frame_resized = cv2.resize(frame, (scaled_width, scaled_height), interpolation=cv2.INTER_LINEAR)
            frame = np.zeros((app.video_label.height(), app.video_label.width(), 3), dtype=np.uint8)
            frame[offset_y:offset_y + scaled_height, offset_x:offset_x + scaled_width] = frame_resized

            if shared_data.video_select:
                x, y = shared_data.video_click_x, shared_data.video_click_y
                user_click_x = (x * scaled_width / original_width) + offset_x
                user_click_y = (y * scaled_height / original_height) + offset_y
                cv2.rectangle(frame, (int(user_click_x) - 25, int(user_click_y) - 25), (int(user_click_x) + 25, int(user_click_y) + 25), (255, 255, 255), 2)

            # Update shared_data to indicate no zoom
            shared_data.video_track_x1 = 0
            shared_data.video_track_y1 = 0
            shared_data.video_zoom_w = original_width
            shared_data.video_zoom_h = original_height
            shared_data.video_scaled_width = scaled_width
            shared_data.video_scaled_height = scaled_height
            shared_data.video_offset_x = offset_x
            shared_data.video_offset_y = offset_y

        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
        app.video_label.setPixmap(QPixmap.fromImage(q_img.scaled(app.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)))
    else:
        app.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart the video
