# main.py
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QSplitter, QMenuBar, QMessageBox, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer, pyqtSlot,  QUrl, pyqtSignal, QObject
from shared_data import shared_data
from connection import setup_video_stream
from telemetry import start_data_thread
#from map_view import MapView, update_map
from user_input import keyPressEvent
from instruments import ArtificialHorizonIndicator
import argparse
import threading
import cv2
import math
import requests
import time
from video import ClickableLabel
from map_server import run_flask, update_position, get_position

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Connection Settings')
        self.layout = QVBoxLayout(self)

        self.entry1 = QLineEdit(self)
        self.entry1.setPlaceholderText('Enter setting 1')
        self.layout.addWidget(self.entry1)

        self.entry2 = QLineEdit(self)
        self.entry2.setPlaceholderText('Enter setting 2')
        self.layout.addWidget(self.entry2)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

    def save_settings(self):
        setting1 = self.entry1.text()
        setting2 = self.entry2.text()
        print(f'Settings saved: {setting1}, {setting2}')
        self.accept()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        start_data_thread(self)
        self.setup_timers()

    def initUI(self):
        self.setWindowTitle('PyQt5 GUI Demo')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: lightgrey;")

        # Menu bar
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("File")
        connection_menu = menu_bar.addMenu("Connection")
        preferences_menu = menu_bar.addMenu("Preferences")
        about_menu = menu_bar.addMenu("About")

        file_menu.addAction("Open", self.show_file_dialog)
        connection_menu.addAction("Settings", self.show_connection_dialog)
        preferences_menu.addAction("Options", self.show_preferences_dialog)
        about_menu.addAction("Info", self.show_about_dialog)

        # Main layout with QSplitter
        main_splitter = QSplitter(Qt.Horizontal, self)
        main_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        # Left Column: Map Display (top) and Video Stream (bottom)
        left_column_splitter = QSplitter(Qt.Vertical)
        left_column_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        self.map_view = QWebEngineView()
        self.map_view.setUrl(QUrl('http://localhost:5000/'))
        left_column_splitter.addWidget(self.map_view)

        # Add a button to clear the destination marker:
        map_buttons_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f'Button {i+1}', self)
            map_buttons_layout.addWidget(btn)
        clear_marker_btn = QPushButton('Clear Marker', self)
        clear_marker_btn.clicked.connect(self.remove_user_marker)
        map_buttons_layout.addWidget(clear_marker_btn)
        map_buttons_widget = QWidget()
        map_buttons_widget.setLayout(map_buttons_layout)
        map_buttons_widget.setFixedHeight(40)
        left_column_splitter.addWidget(map_buttons_widget)


        # Video stream
        self.video_label = setup_video_stream(self, "video.mp4")
        left_column_splitter.addWidget(self.video_label)

        # Video buttons
        video_buttons_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f'Button {i+1}', self)
            video_buttons_layout.addWidget(btn)
        video_buttons_widget = QWidget()
        video_buttons_widget.setLayout(video_buttons_layout)
        video_buttons_widget.setFixedHeight(40)
        left_column_splitter.addWidget(video_buttons_widget)

        main_splitter.addWidget(left_column_splitter)

        # Right Column: Flight Data (top) and Terminal (bottom)
        right_column_splitter = QSplitter(Qt.Vertical)
        right_column_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        # Flight data
        flight_data_splitter = QSplitter(Qt.Vertical)
        flight_data_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        # Important data label
        self.important_data_label = QLabel("NO MODE SET", self)
        self.important_data_label.setAlignment(Qt.AlignCenter)
        self.important_data_label.setStyleSheet("background-color: black; color: white; font-size: 20px; font-weight: bold;")
        self.important_data_label.setFixedHeight(50)
        flight_data_splitter.addWidget(self.important_data_label)

        flight_data_horiz_splitter = QSplitter(Qt.Horizontal)
        flight_data_splitter.addWidget(flight_data_horiz_splitter)

        self.horizon_indicator = ArtificialHorizonIndicator(self)
        flight_data_horiz_splitter.addWidget(self.horizon_indicator)

        flight_data_layout = QVBoxLayout()
        self.speed_label = QLabel("Speed: 0")
        self.altitude_label = QLabel("Altitude: 0")
        self.pitch_label = QLabel("Pitch: 0")
        self.roll_label = QLabel("Roll: 0")
        self.hdg_label = QLabel("Heading: 0")
        self.rssi_label = QLabel("RSSI: 0")
        self.lq_label = QLabel("LQ: 0")
        self.sats_label = QLabel("Sats: 0")
        self.vbat_label = QLabel("VBAT: 0")
        self.cur_label = QLabel("Current: 0")
        self.pct_label = QLabel("Battery %: 0")
        self.mah_label = QLabel("Battery mAh: 0")
        flight_data_layout.addWidget(self.speed_label)
        flight_data_layout.addWidget(self.altitude_label)
        flight_data_layout.addWidget(self.pitch_label)
        flight_data_layout.addWidget(self.roll_label)
        flight_data_layout.addWidget(self.hdg_label)
        flight_data_layout.addWidget(self.rssi_label)
        flight_data_layout.addWidget(self.lq_label)
        flight_data_layout.addWidget(self.vbat_label)
        flight_data_layout.addWidget(self.cur_label)
        flight_data_layout.addWidget(self.pct_label)
        flight_data_layout.addWidget(self.mah_label)
        flight_data_widget = QWidget()
        flight_data_widget.setLayout(flight_data_layout)
        flight_data_horiz_splitter.addWidget(flight_data_widget)

        # Flight data buttons
        flight_data_buttons_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f'Button {i+1}', self)
            flight_data_buttons_layout.addWidget(btn)
        flight_data_buttons_widget = QWidget()
        flight_data_buttons_widget.setLayout(flight_data_buttons_layout)
        flight_data_buttons_widget.setFixedHeight(40)
        flight_data_splitter.addWidget(flight_data_buttons_widget)
        right_column_splitter.addWidget(flight_data_splitter)

        # Terminal
        terminal_layout = QVBoxLayout()
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("background-color: black; color: white;")
        terminal_layout.addWidget(self.terminal_output)
        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.process_command)
        self.terminal_input.setStyleSheet("background-color: black; color: white;")
        terminal_layout.addWidget(self.terminal_input)
        terminal_widget = QWidget()
        terminal_widget.setLayout(terminal_layout)
        right_column_splitter.addWidget(terminal_widget)

        main_splitter.addWidget(right_column_splitter)

        # Set the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setMenuBar(menu_bar)
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def remove_user_marker(self):
        shared_data.user_marker_active = False

    def show_file_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("File Dialog")
        dialog.exec_()

    def show_connection_dialog(self):
        dialog = ConnectionDialog(self)
        dialog.exec_()

    def show_preferences_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences Dialog")
        dialog.exec_()

    def show_about_dialog(self):
        QMessageBox.information(self, "About", "This is a PyQt5 GUI Demo")

    def keyPressEvent(self, event):
        keyPressEvent(self, event)  # Delegate to input handling

    def handle_video_click(self, x, y):
        print(f"Clicked coordinates in original frame: ({x}, {y})")

    def process_command(self):
        command = self.terminal_input.text()
        self.terminal_output.append(f'Command: {command}')
        self.terminal_input.clear()

    def closeEvent(self, event):
        try:
            requests.post('http://localhost:5000/shutdown')
        except requests.exceptions.RequestException as e:
            print(f"Error sending shutdown request: {e}")
        self.cap.release()
        event.accept()

    def setup_timers(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_flight_data)
        self.update_timer.start(100)

    @pyqtSlot()
    def update_flight_data(self):
        #print(shared_data.latitude, shared_data.longitude)
        self.speed_label.setText(f"Speed: {shared_data.gspd:.2f}")
        self.altitude_label.setText(f"Altitude: {shared_data.gps_alt:.2f}")
        self.pitch_label.setText(f"Pitch: {math.degrees(shared_data.pitch):.2f}")
        self.roll_label.setText(f"Roll: {math.degrees(shared_data.roll):.2f}")
        self.hdg_label.setText(f"Heading: {shared_data.hdg:.2f}")
        self.rssi_label.setText(f"RSSI: {shared_data.rssi1:.2f}")
        self.lq_label.setText(f"LQ: {shared_data.lq}")
        self.sats_label.setText(f"Sats: {shared_data.sats}")
        self.vbat_label.setText(f"VBAT: {shared_data.vbat:.2f}")
        self.cur_label.setText(f"Current: {shared_data.curr}")
        self.pct_label.setText(f"Battery %: {shared_data.pct}")
        self.mah_label.setText(f"Battery mAh: {shared_data.mah}")

        self.horizon_indicator.update_horizon()
        update_position(shared_data.latitude, shared_data.longitude)

        if (time.time() - shared_data.last_time_telemetry) > 3:
            shared_data.telemetry_lost = True
        else:
            shared_data.telemetry_lost = False

        if shared_data.telemetry_lost:
            self.important_data_label.setText("TELEMETRY LOST")
        else:
            self.important_data_label.setText(f"MODE {shared_data.flightmode}")

        if shared_data.error or shared_data.telemetry_lost:
            self.important_data_label.setStyleSheet("background-color: red; color: black; font-size: 20px; font-weight: bold;")
        else:
            self.important_data_label.setStyleSheet("background-color: black; color: white; font-size: 20px; font-weight: bold;")


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    time.sleep(1)

    app = QApplication(['', '--no-sandbox'])
    ex = App()
    ex.show()
    sys.exit(app.exec_())
