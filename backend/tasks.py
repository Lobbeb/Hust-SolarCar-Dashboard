import time
from threading import Event
from flask_socketio import SocketIO

from backend.helpers import fetch_all_data


thread_stop_event = Event()

def background_data_fetcher(socketio: SocketIO):
    while not thread_stop_event.is_set():
        time.sleep(2)
        latest_data = fetch_all_data(limit=20)
        if any(latest_data.values()):
            socketio.emit("new_data", latest_data)
#