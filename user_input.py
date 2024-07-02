# input.py
from PyQt5.QtCore import Qt
from shared_data import shared_data

def keyPressEvent(app, event):
    if event.key() == Qt.Key_C:
        shared_data.video_select = False
        print("Key C pressed")
        
    elif event.key() == Qt.Key_D:
        print("Key D pressed")
        #app.dummy_key_function_2()

