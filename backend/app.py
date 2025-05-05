from flask import Flask
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from backend.routes import main, routes
from backend.tasks import background_data_fetcher, thread_stop_event
from backend.socket_events import register_socketio_events
from backend.cleanup import cleanup_old_rows

# Flask + SocketIO setup
app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(main)

#socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

register_socketio_events(socketio)

if __name__ == "__main__":
    # 1) Start your real-time fetcher
    socketio.start_background_task(background_data_fetcher, socketio)

    # 2) Schedule nightly cleanup at 03:00 Stockholm time
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Stockholm"))
    scheduler.add_job(
        cleanup_old_rows,
        trigger="cron",
        hour=3,
        minute=0,
        id="telemetry_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] Cleanup job scheduled for 03:00 Europe/Stockholm daily.")

    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    finally:
        # gracefully stop both
        thread_stop_event.set()
        scheduler.shutdown(wait=False)
        print("Shutting down background thread & scheduler…")
