# shared_data.py
import threading

class SharedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.mode = "ANGLE"
        self.pitch = 0.0
        self.roll = 0.0
        self.telemetry_lost = False
        self.error = False
        self.latitude = 52.52
        self.longitude = 13.405
        self.video_select = False
        self.video_click_x = 0
        self.video_click_y = 0
        self.simulate = False
        self.telemetry = "crsf"  # Can be "random" or "crsf"
        self.last_time_telemetry = 0
        self.gspd = 0.0
        self.hdg = 0.0
        self.gps_alt = 0.0
        self.baro_alt = 0.0
        self.sats = 0
        self.vspd = 0.0
        self.yaw = 0.0
        self.rssi1 = 0.0
        self.rssi2 = 0.0
        self.snr = 0.0
        self.lq = 0.0
        self.vbat = 0.0
        self.curr = 0.0
        self.mah = 0.0
        self.pct = 0.0
        self.flightmode = "NONE"
        self.printtele = False
        self.user_marker_lat = None
        self.user_marker_lon = None
        self.user_marker_active = False
        self.setting_video = 'video.mp4'
        self.setting_tele_port = '/dev/ttyACM0'
        self.setting_tele_baud = 420000

shared_data = SharedData()
