from flask import Flask
from flask_socketio import SocketIO
import logging
import atexit

from backend.routes import main, routes
from backend.tasks import background_data_fetcher, thread_stop_event
from backend.socket_events import register_socketio_events
from backend.config import SECRET_KEY, FLASK_ENV, ENABLE_AUTO_CLEANUP
from backend.helpers import initialize_connection_pool
from backend.database_cleanup import start_automated_cleanup, stop_automated_cleanup

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
    
    # Stop automated cleanup scheduler
    try:
        stop_automated_cleanup()
        logger.info("Automated cleanup scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping cleanup scheduler: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)

if __name__ == "__main__":
    logger.info("Starting HUST Solar Car Dashboard...")
    
    # 1) Start your real-time fetcher
    socketio.start_background_task(background_data_fetcher, socketio)
    logger.info("Background data fetcher started")
    
    # 2) Start automated database cleanup if enabled
    if ENABLE_AUTO_CLEANUP:
        try:
            start_automated_cleanup()
            logger.info("🤖 Automated database cleanup scheduler started (every 7 days at 3:00 AM)")
        except Exception as e:
            logger.error(f"Failed to start automated cleanup: {e}")
    else:
        logger.info("Automated database cleanup is disabled in configuration")

    try:
        is_debug = FLASK_ENV == 'development'
        logger.info(f"Starting server in {'debug' if is_debug else 'production'} mode")
        socketio.run(app, host="0.0.0.0", port=5000, debug=is_debug)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Gracefully stop services
        logger.info("Shutting down services...")
        thread_stop_event.set()
        stop_automated_cleanup()
        logger.info("Shutdown complete")
