# map_view.py
import folium
import threading
from PyQt5.QtCore import QUrl, pyqtSignal, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import os
from shared_data import shared_data

class MapView(QWebEngineView):
    marker_added = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUrl(QUrl('http://localhost:5000/map.html'))
        self.marker = None
        self.destination_marker = None

    def update_marker(self):
        lat, lon = shared_data.latitude, shared_data.longitude
        data = {'latitude': lat, 'longitude': lon}
        with open('marker.json', 'w') as f:
            json.dump(data, f)
        self.page().runJavaScript('updateUAVMarker()')

    def add_marker(self, lat, lon):
        data = {'latitude': lat, 'longitude': lon}
        with open('destination_marker.json', 'w') as f:
            json.dump(data, f)
        self.page().runJavaScript(f'addOrUpdateDestinationMarker({lat}, {lon})')
        self.marker_added.emit(lat, lon)

    def clear_marker(self):
        self.page().runJavaScript('clearDestinationMarker()')

class RequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        if self.path == '/destination_marker.json':
            with open('destination_marker.json', 'w') as f:
                f.write(post_data.decode('utf-8'))
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(501)
            self.end_headers()

def update_map(map_view):
    m = folium.Map(location=[52.52, 13.405], zoom_start=10)
    folium.Marker([52.52, 13.405], tooltip='Berlin', icon=folium.Icon(color='blue')).add_to(m)

    # Save map to HTML file
    map_file = 'map.html'
    m.save(map_file)

    # Add JavaScript to update UAV marker
    with open(map_file, 'a') as f:
        f.write("""
        <div id="map" style="width: 100%; height: 100%;"></div>
        <script>
        var map = L.map('map').setView([52.52, 13.405], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        var uavMarker = L.marker([52.52, 13.405], {icon: L.icon({iconUrl: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'})}).addTo(map);
        var destinationMarker = null;

        function updateUAVMarker() {
            fetch('marker.json').then(response => response.json()).then(data => {
                uavMarker.setLatLng([data.latitude, data.longitude]);
            });
        }

        function addOrUpdateDestinationMarker(lat, lon) {
            if (destinationMarker) {
                destinationMarker.setLatLng([lat, lon]);
            } else {
                destinationMarker = L.marker([lat, lon], {icon: L.icon({iconUrl: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'})}).addTo(map);
            }
        }

        function clearDestinationMarker() {
            if (destinationMarker) {
                map.removeLayer(destinationMarker);
                destinationMarker = null;
            }
        }

        map.on('click', function(e) {
            var lat = e.latlng.lat;
            var lon = e.latlng.lng;
            addOrUpdateDestinationMarker(lat, lon);
            fetch('destination_marker.json', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({latitude: lat, longitude: lon})
            });
        });
        </script>
        """)

    threading.Thread(target=start_http_server, args=(map_file,), daemon=True).start()
    map_view.setUrl(QUrl('http://localhost:8000/map.html'))

def start_http_server(map_file):
    os.chdir(os.path.dirname(os.path.abspath(map_file)))
    handler = RequestHandler
    httpd = HTTPServer(('localhost', 8000), handler)
    httpd.serve_forever()
