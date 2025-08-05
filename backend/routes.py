from flask import Blueprint, render_template, request, jsonify, make_response
import logging
import time
from datetime import datetime
from functools import wraps
from backend.helpers import fetch_all_data, health_check
from backend.config import RATE_LIMIT_PER_MINUTE

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)
routes = Blueprint('routes', __name__)

# Simple rate limiting storage (in production, use Redis)
rate_limit_storage = {}

def rate_limit(max_requests=RATE_LIMIT_PER_MINUTE):
    """Simple rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries (older than 1 minute)
            cutoff_time = current_time - 60
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage.get(client_ip, [])
                if req_time > cutoff_time
            ]
            
            # Check rate limit
            if len(rate_limit_storage.get(client_ip, [])) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            rate_limit_storage[client_ip].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

@routes.route("/")
def index():
    return render_template("index.html")

@main.route("/health")
def health_check_endpoint():
    """Health check endpoint for monitoring"""
    try:
        db_healthy = health_check()
        status = 'healthy' if db_healthy else 'unhealthy'
        status_code = 200 if db_healthy else 503
        
        return jsonify({
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if db_healthy else 'disconnected',
            'version': '1.0.0'
        }), status_code
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500




@main.route("/data")
@rate_limit()
def get_data():
    """Get telemetry data with validation"""
    try:
        limit = request.args.get("limit", default=20, type=int)
        
        # Validate limit parameter
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'Limit must be between 1 and 1000'}), 400
        
        data = fetch_all_data(limit=limit)
        
        # Log successful request
        logger.debug(f"Data request successful: limit={limit}, IP={request.remote_addr}")
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@main.route("/export_csv")
@rate_limit(max_requests=5)  # Lower limit for export
def export_csv():
    """Export data as CSV with enhanced error handling"""
    try:
        limit = request.args.get("limit", default=100, type=int)
        
        # Validate limit for CSV export
        if limit < 1 or limit > 5000:
            return jsonify({'error': 'CSV export limit must be between 1 and 5000'}), 400
        
        data_rows = fetch_all_data(limit=limit)
        csv_lines = ["Table,ID,Timestamp,Value1,Value2\n"]

        # Add battery data
        for row in data_rows["battery_data"]:
            csv_lines.append(f"Battery,{row['id']},{row['timestamp']},{row['battery_volt']},{row['battery_current']}\n")

        # Add motor data
        for row in data_rows["motor_data"]:
            csv_lines.append(f"Motor,{row['id']},{row['timestamp']},{row['motor_current']},{row['motor_temp']}\n")
        
        # Add MPPT data
        for row in data_rows["mppt_data"]:
            csv_lines.append(f"MPPT,{row['id']},{row['timestamp']},{row['MPPT_total_watt']},{row['MPPT1_watt']}\n")
        
        # Add vehicle data
        for row in data_rows["vehicle_data"]:
            csv_lines.append(f"Vehicle,{row['id']},{row['timestamp']},{row['velocity']},{row['distance_travelled']}\n")

        resp = make_response("".join(csv_lines))
        resp.headers["Content-Disposition"] = f"attachment; filename=hust_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        resp.mimetype = "text/csv"
        
        logger.info(f"CSV export successful: {len(csv_lines)} rows, IP={request.remote_addr}")
        return resp
        
    except Exception as e:
        logger.error(f"Error in export_csv: {e}")
        return jsonify({'error': 'Export failed'}), 500
