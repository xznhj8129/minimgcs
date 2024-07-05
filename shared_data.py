# shared_data.py
import threading
import geospatial

class SharedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.telemetry = "random"  # Can be "random" or "crsf"
        self.telemetry_connected = False
        self.last_time_telemetry = 0
        self.mode = "ANGLE"
        self.pitch = 0.0
        self.roll = 0.0
        self.telemetry_lost = False
        self.error = False
        self.got_gps = False
        self.pos_uav = geospatial.GPSposition(0,0,0)
        self.pos_marker = geospatial.GPSposition(0,0,0)
        self.pos_home = geospatial.GPSposition(0,0,0)
        self.pos_goto = geospatial.GPSposition(0,0,0)
        self.pos_poi = geospatial.GPSposition(0,0,0)
        self.wp_n = 0
        self.pos_wp = geospatial.GPSposition(0,0,0)
        self.video_select = False
        self.video_click_x = 0
        self.video_click_y = 0
        self.gspd = 0.0
        self.hdg = 0.0
        self.baro_alt = 0.0
        self.sats = 0
        self.vspd = 0.0
        self.yaw = 0.0
        self.rssi1 = 0.0
        self.rssi2 = 0.0
        self.snr = 0.0
        self.lq = 0.0
        self.scells = 3
        self.vbat = 0.0
        self.curr = 0.0
        self.mah = 0.0
        self.pct = 0.0
        self.flightmode = "NONE"
        self.printtele = False
        self.user_marker_active = False
        self.setting_video = 'video.mp4'
        self.setting_tele_port = '/dev/ttyACM0'
        self.setting_tele_baud = 420000

shared_data = SharedData()
