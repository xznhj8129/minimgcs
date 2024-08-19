from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading, os
from shared_data import shared_data

app = Flask(__name__)
CORS(app)

def update_position(lat, lon, alt):
    with shared_data.lock:
        shared_data.pos_uav.lat = lat
        shared_data.pos_uav.lon = lon
        shared_data.pos_uav.alt = alt

def get_position():
    with shared_data.lock:
        return shared_data.pos_uav.lat, shared_data.pos_uav.lon

def set_user_marker(lat, lon):
    with shared_data.lock:
        shared_data.pos_marker.lat = lat
        shared_data.pos_marker.lon = lon
        shared_data.user_marker_active = True
        print("User point:", lat, lon)

def get_user_marker():
    with shared_data.lock:
        return shared_data.pos_marker.lat, shared_data.pos_marker.lon, shared_data.user_marker_active

@app.route('/')
def index():
    lat, lon = get_position()
    return render_template('map.html', latitude=lat, longitude=lon)

@app.route('/update_marker')
def update_marker():
    lat, lon = get_position()
    user_lat, user_lon, user_active = get_user_marker()
    response = {
        'latitude': lat,
        'longitude': lon,
        'yaw': shared_data.hdg,
        'user_latitude': user_lat,
        'user_longitude': user_lon,
        'user_active': user_active,
        'got_gps': shared_data.got_gps,
        'map_center': shared_data.map_center,
        'home_set': shared_data.home_set,
        'home_lat': shared_data.pos_home.lat,
        'home_lon': shared_data.pos_home.lon,
        'goto_set': shared_data.goto_set,
        'goto_lat': shared_data.pos_goto.lat,
        'goto_lon': shared_data.pos_goto.lon,
        'poi_set': shared_data.poi_set,
        'poi_lat': shared_data.pos_poi.lat,
        'poi_lon': shared_data.pos_poi.lon,
        'wp_set': shared_data.wp_set,
        'wp_lat': shared_data.pos_wp.lat,
        'wp_lon': shared_data.pos_wp.lon
    }
    return jsonify(response)

@app.route('/set_position', methods=['POST'])
def set_position():
    data = request.json
    lat = data['latitude']
    lon = data['longitude']
    set_user_marker(lat, lon)
    return jsonify({'status': 'success'})

@app.route('/remove_marker', methods=['POST'])
def remove_marker():
    remove_user_marker()
    return jsonify({'status': 'success'})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os._exit(0)
    return jsonify({'status': 'success'})

def run_flask():
    app.run(threaded=True)
