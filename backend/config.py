
# ============ CONFIG ============
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Flask Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# Application Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_DB_CONNECTIONS = int(os.getenv("MAX_DB_CONNECTIONS", "10"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# Validate required environment variables
required_vars = [DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]
if not all(required_vars):
    missing = [var for var in ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"] 
               if not os.getenv(var)]
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
