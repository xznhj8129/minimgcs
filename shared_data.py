# shared_data.py
import threading
import geospatial

class SharedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.video_source = "/dev/video0"
        self.telem_port = "/dev/ttyACM0"
        self.telem_baud = 420000
        self.telemetry = "random"  # Can be "random" or "crsf"
        self.telemetry_connected = False
        self.error = False
        self.got_gps = False
        self.last_time_telemetry = 0
        self.mode = "ANGLE"
        self.pitch = 0.0
        self.roll = 0.0
        self.telemetry_lost = False
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
        self.video_track_zoom_active = False
        self.video_track_zoom_level = 1.0
        self.video_track_x = 0
        self.video_track_y = 0
        self.video_track_x1 = 0
        self.video_track_y1 = 0
        self.video_zoom_w = 0
        self.video_zoom_h = 0

        self.gspd = 0.0
        self.hdg = 0.0
        self.baro_alt = 0.0
        self.sats = 12
        self.vspd = 0.0
        self.yaw = 0.0
        self.rssi1 = -10.0
        self.rssi2 = 0.0
        self.snr = 0.0
        self.lq = 100
        self.scells = 3
        self.vbat = 0.0
        self.curr = 0.0
        self.mah = 0.0
        self.pct = 0.0
        
        self.warn_vcell = 3.5
        self.warn_vbat = self.warn_vcell * self.scells
        self.flightmode = "NONE"
        self.printtele = False

shared_data = SharedData()
