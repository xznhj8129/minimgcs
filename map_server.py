from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading, os
from shared_data import shared_data

app = Flask(__name__)
CORS(app)

def update_position(lat, lon):
    with shared_data.lock:
        shared_data.latitude = lat
        shared_data.longitude = lon

def get_position():
    with shared_data.lock:
        return shared_data.latitude, shared_data.longitude

def set_user_marker(lat, lon):
    with shared_data.lock:
        shared_data.user_marker_lat = lat
        shared_data.user_marker_lon = lon
        shared_data.user_marker_active = True
        print("User point:",lat,lon)

def get_user_marker():
    with shared_data.lock:
        return shared_data.user_marker_lat, shared_data.user_marker_lon, shared_data.user_marker_active

def remove_user_marker():
    with shared_data.lock:
        shared_data.user_marker_active = False

@app.route('/')
def index():
    lat, lon = get_position()
    return render_template('map.html', latitude=lat, longitude=lon)

@app.route('/update_marker')
def update_marker():
    lat, lon = get_position()
    user_lat, user_lon, user_active = get_user_marker()
    return jsonify({
        'latitude': lat, 
        'longitude': lon, 
        'user_latitude': user_lat, 
        'user_longitude': user_lon, 
        'user_active': user_active
    })

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
    

    