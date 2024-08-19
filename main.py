# main.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QAction, 
                             QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QWidget, 
                             QPushButton, QTextEdit, QLineEdit, QMessageBox, QDialog)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer, pyqtSlot,  QUrl, pyqtSignal, QObject
from shared_data import shared_data
from telemetry import start_data_thread
from user_input import keyPressEvent
from instruments import ArtificialHorizonIndicator
from settings import ConnectionDialog
from video import ClickableLabel, setup_video_stream
from map_server import run_flask, update_position, get_position
import argparse
import threading
import cv2
import math
import requests
import geospatial
import time


class App(QWidget):
    def __init__(self):
        super().__init__()
        start_data_thread(self)
        self.setup_timers()
        self.is_video_maximized = False
        self.left_column_splitter = None
        self.right_column_splitter = None
        self.video_label = None
        self.main_splitter = None
        self.video_container_widget = None
        self.map_container_widget = None
        self.flight_data_container_widget = None
        self.terminal_container_widget = None
        self.zoom_factor = 1.0
        self.warnstyle_off = "background-color: black; color: white; font-size: 20px; border: 3px white; font-weight: bold;"
        self.warnstyle_on = "background-color: red; color: black; font-size: 20px; border-width: 2px; border-color: black; font-weight: bold;"

        self.initUI()

    def initUI(self):
        self.setWindowTitle('MinimGCS')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: lightgrey;")

        menu_bar = self.setup_menu_bar()

        self.main_splitter = QSplitter(Qt.Horizontal, self)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        self.setup_left_column()
        self.setup_center_column()
        self.setup_right_column()

        main_layout = QVBoxLayout(self)
        main_layout.setMenuBar(menu_bar)
        main_layout.addWidget(self.main_splitter)
        self.setLayout(main_layout)

    def setup_menu_bar(self):
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("File")
        connection_menu = menu_bar.addMenu("Connection")
        preferences_menu = menu_bar.addMenu("Preferences")
        about_menu = menu_bar.addMenu("About")

        file_menu.addAction("Open", self.show_file_dialog)
        connection_menu.addAction("Settings", self.show_connection_dialog)
        preferences_menu.addAction("Options", self.show_preferences_dialog)
        about_menu.addAction("Info", self.show_about_dialog)

        return menu_bar

    def setup_left_column(self):
        self.left_column_splitter = QSplitter(Qt.Vertical)
        self.left_column_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        self.map_view = QWebEngineView()
        self.map_view.setUrl(QUrl('http://localhost:5000/'))
        self.left_column_splitter.addWidget(self.map_view)

        map_info_widget = self.setup_map_info()
        self.left_column_splitter.addWidget(map_info_widget)

        map_buttons_widget = self.setup_map_buttons()
        self.left_column_splitter.addWidget(map_buttons_widget)

        self.main_splitter.addWidget(self.left_column_splitter)

    def setup_map_info(self):
        map_info_layout = QHBoxLayout()

        self.distance_to_home_label = QLabel("Distance to home: 0", self)
        self.distance_to_marker_label = QLabel("Distance to marker: 0", self)
        self.gps_label = QLabel("GPS: 0,0", self)
        #self.mgrs_label = QLabel("MGRS: 0", self)

        map_info_layout.addWidget(self.distance_to_home_label)
        map_info_layout.addSpacing(10)  # Fixed distance between labels
        map_info_layout.addWidget(self.distance_to_marker_label)
        map_info_layout.addSpacing(10)  # Fixed distance between labels
        map_info_layout.addWidget(self.gps_label)
        #map_info_layout.addSpacing(10)  # Fixed distance between labels
        #map_info_layout.addWidget(self.mgrs_label)

        map_info_widget = QWidget()
        map_info_widget.setLayout(map_info_layout)
        map_info_widget.setFixedHeight(40)

        return map_info_widget

    def setup_map_buttons(self):
        map_buttons_layout = QHBoxLayout()

        self.btn_goto_marker = QPushButton('GOTO', self)
        self.btn_poi_marker = QPushButton('Set POI', self)
        self.btn_home_marker = QPushButton('Set Home', self)
        self.btn_clear_marker = QPushButton('Clear Marker', self)
        self.btn_view_lock = QPushButton('View lock', self)

        self.btn_goto_marker.clicked.connect(self.marker_set_goto)
        self.btn_poi_marker.clicked.connect(self.marker_set_poi)
        self.btn_home_marker.clicked.connect(self.marker_set_home)
        self.btn_clear_marker.clicked.connect(self.remove_user_marker)
        self.btn_view_lock.clicked.connect(self.map_view_lock)

        map_buttons_layout.addWidget(self.btn_goto_marker)
        map_buttons_layout.addWidget(self.btn_poi_marker)
        map_buttons_layout.addWidget(self.btn_home_marker)
        map_buttons_layout.addWidget(self.btn_clear_marker)
        map_buttons_layout.addWidget(self.btn_view_lock)

        map_buttons_widget = QWidget()
        map_buttons_widget.setLayout(map_buttons_layout)
        map_buttons_widget.setFixedHeight(40)
        
        return map_buttons_widget

    def setup_center_column(self):
        self.center_column_splitter = QSplitter(Qt.Vertical)
        self.center_column_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")

        flight_data_widget = self.setup_flight_data()
        self.center_column_splitter.addWidget(flight_data_widget)

        wp_widget = self.setup_warning_panel()
        self.center_column_splitter.addWidget(wp_widget)

        terminal_widget = self.setup_terminal()
        self.center_column_splitter.addWidget(terminal_widget)

        self.main_splitter.addWidget(self.center_column_splitter)

    def setup_critical_info(self):
        critical_info_layout = QHBoxLayout()

        self.ci_vbat_label = QLabel("VBAT 12.6", self)
        self.ci_vbat_label.setAlignment(Qt.AlignCenter)
        self.ci_vcell_label = QLabel("VCELL 4.2", self)
        self.ci_vcell_label.setAlignment(Qt.AlignCenter)
        self.ci_rssi_label = QLabel("RSSI -10", self)
        self.ci_rssi_label.setAlignment(Qt.AlignCenter)
        self.ci_lq_label = QLabel("LQ 100", self)
        self.ci_lq_label.setAlignment(Qt.AlignCenter)

        critical_info_layout.addWidget(self.ci_vbat_label)
        critical_info_layout.addSpacing(10)
        critical_info_layout.addWidget(self.ci_vcell_label)
        critical_info_layout.addSpacing(10)
        critical_info_layout.addWidget(self.ci_rssi_label)
        critical_info_layout.addSpacing(10)
        critical_info_layout.addWidget(self.ci_lq_label)

        critical_info_widget = QWidget()
        critical_info_widget.setStyleSheet(self.warnstyle_off)
        critical_info_widget.setLayout(critical_info_layout)
        critical_info_widget.setFixedHeight(40)

        return critical_info_widget

    def setup_status_label(self):
        status_label = QHBoxLayout()

        self.status_mode = QLabel("NO MODE SET", self)
        self.status_mode.setAlignment(Qt.AlignCenter)
        self.ctrl_mode = QLabel("RX DIRECT", self)
        self.ctrl_mode.setAlignment(Qt.AlignCenter)

        status_label.addWidget(self.status_mode)
        status_label.addSpacing(10)
        status_label.addWidget(self.ctrl_mode)

        status_widget = QWidget()
        status_widget.setStyleSheet("font-size: 20px; font-weight: bold;")
        status_widget.setLayout(status_label)
        status_widget.setStyleSheet(self.warnstyle_off)
        status_widget.setFixedHeight(40)

        return status_widget


    def setup_flight_data(self):
        flight_data_splitter = QSplitter(Qt.Vertical)
        flight_data_splitter.setStyleSheet("QSplitter::handle { background-color: grey; }")
        
        self.status_widget = self.setup_status_label()
        flight_data_splitter.addWidget(self.status_widget)

        self.critical_info_widget = self.setup_critical_info()
        flight_data_splitter.addWidget(self.critical_info_widget)

        flight_data_horiz_splitter = QSplitter(Qt.Horizontal)
        flight_data_splitter.addWidget(flight_data_horiz_splitter)

        self.horizon_indicator = ArtificialHorizonIndicator(self)
        flight_data_horiz_splitter.addWidget(self.horizon_indicator)

        flight_data_widget = self.setup_flight_data_labels()
        flight_data_horiz_splitter.addWidget(flight_data_widget)

        flight_data_buttons_widget = self.setup_flight_data_buttons()
        flight_data_splitter.addWidget(flight_data_buttons_widget)

        return flight_data_splitter

    def setup_flight_data_labels(self):
        flight_data_layout = QVBoxLayout()
        self.speed_label = QLabel("Speed: 0")
        self.altitude_label = QLabel("Altitude: 0")
        self.pitch_label = QLabel("Pitch: 0")
        self.roll_label = QLabel("Roll: 0")
        self.yaw_label = QLabel("Yaw: 0")
        self.hdg_label = QLabel("Heading: 0")
        self.rssi_label = QLabel("RSSI: 0")
        self.lq_label = QLabel("LQ: 0")
        self.sats_label = QLabel("Sats: 0")
        self.vbat_label = QLabel("VBAT: 0")
        self.cur_label = QLabel("CUR: 0")
        self.pct_label = QLabel("BAT %: 0")
        self.mah_label = QLabel("BAT mAh: 0")
        self.tt_label = QLabel("TELE sec: 0")
        flight_data_layout.addWidget(self.speed_label)
        flight_data_layout.addWidget(self.altitude_label)
        flight_data_layout.addWidget(self.pitch_label)
        flight_data_layout.addWidget(self.roll_label)
        flight_data_layout.addWidget(self.yaw_label)
        flight_data_layout.addWidget(self.hdg_label)
        flight_data_layout.addWidget(self.rssi_label)
        flight_data_layout.addWidget(self.lq_label)
        flight_data_layout.addWidget(self.sats_label)
        flight_data_layout.addWidget(self.vbat_label)
        flight_data_layout.addWidget(self.cur_label)
        flight_data_layout.addWidget(self.pct_label)
        flight_data_layout.addWidget(self.mah_label)
        flight_data_layout.addWidget(self.tt_label)
        flight_data_widget = QWidget()
        flight_data_widget.setLayout(flight_data_layout)

        return flight_data_widget

    def setup_warning_panel(self):
        main_panel = QVBoxLayout()

        # First row
        warning_panel1 = QHBoxLayout()
        self.warn_ind_vbat = QLabel("BATTERY")
        self.warn_ind_lq = QLabel("LQ")
        self.warn_ind_rssi = QLabel("RSSI")

        self.warn_ind_vbat.setStyleSheet(self.warnstyle_off)
        self.warn_ind_lq.setStyleSheet(self.warnstyle_off)
        self.warn_ind_rssi.setStyleSheet(self.warnstyle_off)
        self.warn_ind_vbat.setAlignment(Qt.AlignCenter)
        self.warn_ind_lq.setAlignment(Qt.AlignCenter)
        self.warn_ind_rssi.setAlignment(Qt.AlignCenter)
        
        warning_panel1.addWidget(self.warn_ind_vbat)
        warning_panel1.addSpacing(10)
        warning_panel1.addWidget(self.warn_ind_lq)
        warning_panel1.addSpacing(10)
        warning_panel1.addWidget(self.warn_ind_rssi)

        warning_panel2 = QHBoxLayout()
        self.warn_ind_tele = QLabel("TELE")
        self.warn_ind_sensor = QLabel("SENSOR")
        self.warn_ind_gps = QLabel("GPS")

        self.warn_ind_tele.setStyleSheet(self.warnstyle_off)
        self.warn_ind_sensor.setStyleSheet(self.warnstyle_off)
        self.warn_ind_gps.setStyleSheet(self.warnstyle_off)
        self.warn_ind_tele.setAlignment(Qt.AlignCenter)
        self.warn_ind_sensor.setAlignment(Qt.AlignCenter)
        self.warn_ind_gps.setAlignment(Qt.AlignCenter)
        
        warning_panel2.addWidget(self.warn_ind_tele)
        warning_panel2.addSpacing(10)
        warning_panel2.addWidget(self.warn_ind_sensor)
        warning_panel2.addSpacing(10)
        warning_panel2.addWidget(self.warn_ind_gps)

        # Add both rows to the main panel
        main_panel.addLayout(warning_panel1)
        main_panel.addSpacing(10)
        main_panel.addLayout(warning_panel2)

        warning_panel_widget = QWidget()
        warning_panel_widget.setStyleSheet(self.warnstyle_off)
        warning_panel_widget.setLayout(main_panel)
        return warning_panel_widget

    def setup_flight_data_buttons(self):
        flight_data_buttons_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f'Button {i+1}', self)
            flight_data_buttons_layout.addWidget(btn)


        self.btn_msp_override = QPushButton('MSP Override', self)
        #self.btn_msp_override.clicked.connect(self.toggle_video_trackzoom)
        flight_data_buttons_layout.addWidget(self.btn_msp_override)

        flight_data_buttons_widget = QWidget()
        flight_data_buttons_widget.setLayout(flight_data_buttons_layout)
        flight_data_buttons_widget.setFixedHeight(40)

        return flight_data_buttons_widget

    def setup_terminal(self):
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

        return terminal_widget

    def setup_right_column(self):
        self.video_container_widget = self.setup_video_container()
        self.main_splitter.addWidget(self.video_container_widget)

    def setup_video_container(self):
        video_container_widget = QWidget()
        video_container_layout = QVBoxLayout(video_container_widget)

        self.video_label = setup_video_stream(self, shared_data.video_source)
        video_container_layout.addWidget(self.video_label)

        video_buttons_widget = self.setup_video_buttons()
        video_container_layout.addWidget(video_buttons_widget)

        return video_container_widget

    def setup_video_buttons(self):
        video_buttons_layout = QHBoxLayout()
        for i in range(2):
            btn = QPushButton(f'Button {i+1}', self)
            video_buttons_layout.addWidget(btn)

        self.btn_video_source1 = QPushButton('Cam 1', self)
        self.btn_video_source1.clicked.connect(self.set_video_source1)
        video_buttons_layout.addWidget(self.btn_video_source1)

        self.btn_video_source2 = QPushButton('Cam 2', self)
        self.btn_video_source2.clicked.connect(self.set_video_source2)
        video_buttons_layout.addWidget(self.btn_video_source2)

        self.btn_video_zoom = QPushButton('Zoom', self)
        self.btn_video_zoom.clicked.connect(self.toggle_video_trackzoom)
        video_buttons_layout.addWidget(self.btn_video_zoom)

        self.btn_video_trackzoom = QPushButton('Track', self)
        self.btn_video_trackzoom.clicked.connect(self.toggle_video_trackzoom)
        video_buttons_layout.addWidget(self.btn_video_trackzoom)

        self.btn_video_maximize = QPushButton('Maximize Video', self)
        self.btn_video_maximize.clicked.connect(self.toggle_video_maximization)
        video_buttons_layout.addWidget(self.btn_video_maximize)

        video_buttons_widget = QWidget()
        video_buttons_widget.setLayout(video_buttons_layout)
        video_buttons_widget.setFixedHeight(40)

        return video_buttons_widget

    def toggle_video_trackzoom(self):
        shared_data.video_track_zoom_active = not shared_data.video_track_zoom_active

    def toggle_video_maximization(self):
        if self.is_video_maximized:
            # Restore original layout
            self.main_splitter.insertWidget(0, self.left_column_splitter)
            self.main_splitter.insertWidget(1, self.center_column_splitter)
            self.main_splitter.insertWidget(2, self.video_container_widget)
            self.btn_video_maximize.setText('Maximize Video')
            self.left_column_splitter.show()
            self.center_column_splitter.show()
        else:
            # Hide other widgets and only show video_container_widget
            self.left_column_splitter.hide()
            self.center_column_splitter.hide()
            self.main_splitter.insertWidget(0, self.video_container_widget)
            self.btn_video_maximize.setText('Minimize Video')
        self.is_video_maximized = not self.is_video_maximized

    def map_view_lock(self):
        shared_data.map_center = not shared_data.map_center

    def marker_set_goto(self):
        shared_data.pos_goto = geospatial.GPSposition(shared_data.pos_marker.lat,shared_data.pos_marker.lon,0)
        shared_data.goto_set = True
        shared_data.user_marker_active = False

    def marker_set_poi(self):
        shared_data.pos_poi = geospatial.GPSposition(shared_data.pos_marker.lat,shared_data.pos_marker.lon,0)
        shared_data.poi_set = True
        shared_data.user_marker_active = False

    def marker_set_home(self):
        shared_data.pos_home = geospatial.GPSposition(shared_data.pos_marker.lat,shared_data.pos_marker.lon,0)
        shared_data.home_set = True
        shared_data.user_marker_active = False

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
        
    def handle_zoom_change(self, zoom_factor):
        self.zoom_factor = zoom_factor

    
    def set_video_source1(self):
        pass
    def set_video_source2(self):
        pass

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

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.update_button_color)
        self.timer2.start(100)

    def update_button_color(self):
        if shared_data.video_track_zoom_active:
            self.btn_video_trackzoom.setStyleSheet('background-color: red')
        else:
            self.btn_video_trackzoom.setStyleSheet('')
        
        if shared_data.map_center:
            self.btn_view_lock.setStyleSheet('background-color: red')
        else:
            self.btn_view_lock.setStyleSheet('')

        if shared_data.map_center:
            self.btn_view_lock.setStyleSheet('background-color: red')
        else:
            self.btn_view_lock.setStyleSheet('')

    def play_alarm(self):
        pass

    @pyqtSlot()
    def update_flight_data(self):
        vbat = shared_data.vbat
        cellv = vbat/shared_data.scells
        gps = shared_data.pos_uav
        lq = shared_data.lq

        # Set pfd info
        self.speed_label.setText(f"Speed: {shared_data.gspd:.2f}")
        self.altitude_label.setText(f"Altitude: {shared_data.pos_uav.alt:.2f}")
        self.pitch_label.setText(f"Pitch: {math.degrees(shared_data.pitch):.2f}")
        self.roll_label.setText(f"Roll: {math.degrees(shared_data.roll):.2f}")
        self.yaw_label.setText(f"Yaw: {shared_data.yaw:.2f}")
        self.hdg_label.setText(f"Heading: {shared_data.hdg:.2f}")
        self.rssi_label.setText(f"RSSI: {shared_data.rssi1:.2f}")
        self.lq_label.setText(f"LQ: {lq}")
        self.sats_label.setText(f"Sats: {shared_data.sats}")
        self.vbat_label.setText(f"VBAT: {vbat:.2f}")
        self.cur_label.setText(f"CUR: {shared_data.curr}")
        self.pct_label.setText(f"BAT %: {shared_data.pct}")
        self.mah_label.setText(f"BAT mAh: {shared_data.mah}")
        self.tt_label.setText(f"TELE sec: {round(time.time() - shared_data.last_time_telemetry,1)}")

        self.horizon_indicator.update_horizon()

        # set map info
        try:
            vechome = geospatial.gps_to_vector(gps, shared_data.pos_home)
        except:
            vechome = geospatial.PosVector(0,0,0)
        try:
            vecmarker = geospatial.gps_to_vector(gps, shared_data.pos_marker)
        except:
            vecmarker = geospatial.PosVector(0,0,0)

        self.distance_to_home_label.setText(f"Home: {round(vechome.dist)} m")
        self.distance_to_marker_label.setText(f"Marker: {round(vecmarker.dist)} m")
        self.gps_label.setText(f"GPS: {gps.lat:.8f}, {gps.lon:.8f}")

        # set status info
        if (time.time() - shared_data.last_time_telemetry) > 3:
            shared_data.telemetry_lost = True
        else:
            shared_data.telemetry_lost = False

        if shared_data.error or shared_data.telemetry_lost:
            self.status_mode.setText("TELEMETRY LOST")
            self.status_mode.setStyleSheet(self.warnstyle_on)
        else:
            self.status_mode.setText(f"MODE {shared_data.flightmode}")
            self.status_mode.setStyleSheet(self.warnstyle_off)

        # set critical info
        self.ci_vbat_label.setText(f"BAT {vbat:.2f} V")
        self.ci_vcell_label.setText(f"CELL {cellv:.2f} V")
        self.ci_rssi_label.setText(f"RSSI {shared_data.rssi1:.1f}")
        self.ci_lq_label.setText(f"LQ {lq}")

        if shared_data.vbat <= shared_data.warn_vbat: 
            self.ci_vbat_label.setStyleSheet(self.warnstyle_on)
            self.ci_vcell_label.setStyleSheet(self.warnstyle_on)
        else:
            self.ci_vbat_label.setStyleSheet(self.warnstyle_off)
            self.ci_vcell_label.setStyleSheet(self.warnstyle_off)
        
        if shared_data.rssi1 < shared_data.warn_rssi:
            self.ci_rssi_label.setStyleSheet(self.warnstyle_on)
        else:
            self.ci_rssi_label.setStyleSheet(self.warnstyle_off)
        
        if lq < shared_data.warn_lq:
            self.ci_lq_label.setStyleSheet(self.warnstyle_on)
        else:
            self.ci_lq_label.setStyleSheet(self.warnstyle_off)


        # Warning indicators


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    time.sleep(1)

    app = QApplication(['', '--no-sandbox'])
    ex = App()
    ex.show()
    sys.exit(app.exec_())
