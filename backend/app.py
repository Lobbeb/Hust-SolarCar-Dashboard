from flask import Flask
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import logging
import atexit

from backend.routes import main, routes
from backend.tasks import background_data_fetcher, thread_stop_event
from backend.socket_events import register_socketio_events
from backend.cleanup import cleanup_old_rows
from backend.config import SECRET_KEY, FLASK_ENV
from backend.helpers import initialize_connection_pool

logger = logging.getLogger(__name__)

# Flask + SocketIO setup
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.register_blueprint(routes)
app.register_blueprint(main)

# Initialize database connection pool
try:
    initialize_connection_pool()
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    raise

#socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

register_socketio_events(socketio)

def cleanup_on_exit():
    """Cleanup function to run on application exit"""
    logger.info("Application shutting down...")
    thread_stop_event.set()

# Register cleanup function
atexit.register(cleanup_on_exit)

if __name__ == "__main__":
    logger.info("Starting HUST Solar Car Dashboard...")
    
    # 1) Start your real-time fetcher
    socketio.start_background_task(background_data_fetcher, socketio)
    logger.info("Background data fetcher started")

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
    logger.info("Cleanup job scheduled for 03:00 Europe/Stockholm daily")

    try:
        is_debug = FLASK_ENV == 'development'
        logger.info(f"Starting server in {'debug' if is_debug else 'production'} mode")
        socketio.run(app, host="0.0.0.0", port=5000, debug=is_debug)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # gracefully stop both
        logger.info("Shutting down services...")
        thread_stop_event.set()
        if 'scheduler' in locals():
            scheduler.shutdown(wait=False)
        logger.info("Shutdown complete")
