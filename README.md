# minimgcs
Simple INAV GCS with PyQt and Folium
Meant to be used with CRSF telemetry and a video source such as Digital or OTG receiver
Heavily WIP, 90% is placeholder/unfinished
CRSF telemetry parsing from https://github.com/crsf-wg/crsf/wiki/Python-Parser
This product can expose you to ChatGPT-written code, which is known to the State of California to cause cancer.

## Requirements:
PyQt5
Flask
Flask-CORS
Folium
geographiclib
geojson
MGRS


## Screens:
- Map
- PFD
- Terminal?
- Video

## ToDo:
- Test with HITL
- Audio alarms
- Usable config dialogs
- Integrate functions with UNAVlib and use it
- Tolerable PFD
- Integrate MCVST
- Additional rxo telemetry options
- 2-way link support

## Screens and buttons:
### Map:
- GOTO
- Set POI
- Set Home
- Clear marker
- Maximize
- Lock view

### Video:
- Source
- Zoom
- Maximize

## Primary Flight Display:


## idk
Mode: MONITOR (receive only), CONTROL (2-way control)
uav control: RX DIRECT, DATALINK
