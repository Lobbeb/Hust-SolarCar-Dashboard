from flask_socketio import SocketIO

def register_socketio_events(socketio: SocketIO):
    @socketio.on("connect")
    def on_connect():
        print("Client connected")

    @socketio.on("disconnect")
    def on_disconnect():
        print("Client disconnected")
