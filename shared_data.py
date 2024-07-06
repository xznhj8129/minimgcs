# shared_data.py
import threading
import geospatial

class SharedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.video_source = "video.mp4"
        self.telem_port = "/dev/ttyACM0"
        self.telem_baud = 420000
        self.telemetry = "random"  # Can be "random" or "crsf"
        self.telemetry_connected = False
        self.last_time_telemetry = 0
        self.mode = "ANGLE"
        self.pitch = 0.0
        self.roll = 0.0
        self.telemetry_lost = False
        self.error = False
        self.got_gps = False
        self.map_center = False
        self.pos_uav = geospatial.GPSposition(0,0,0)
        self.user_marker_active = False
        self.pos_marker = geospatial.GPSposition(0,0,0)
        self.home_set = False
        self.pos_home = geospatial.GPSposition(0,0,0)
        self.goto_set = False
        self.pos_goto = geospatial.GPSposition(0,0,0)
        self.poi_set = False
        self.pos_poi = geospatial.GPSposition(0,0,0)
        self.wp_set = False
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

shared_data = SharedData()
