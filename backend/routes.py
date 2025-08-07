from flask import Blueprint, render_template, request, jsonify, make_response
import logging
import time
from datetime import datetime
from functools import wraps
from backend.helpers import fetch_all_data, health_check
from backend.config import RATE_LIMIT_PER_MINUTE
from backend.database_cleanup import (
    run_cleanup, 
    get_database_stats, 
    get_cleanup_recommendations,
    start_automated_cleanup,
    stop_automated_cleanup
)

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
            'version': '2.0.0',
            'features': ['BWSC_Racing', 'Database_Cleanup', 'Latest_Records_Protection']
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


# ===== DATABASE CLEANUP ENDPOINTS =====

@main.route("/admin/cleanup/stats", methods=['GET'])
@rate_limit(max_requests=10)  # Limited access for admin endpoints
def get_cleanup_stats():
    """Get detailed database statistics for cleanup analysis"""
    try:
        stats = get_database_stats()
        total_records = sum(table['total_records'] for table in stats.values())
        total_deletable = sum(table['records_to_delete'] for table in stats.values())
        
        response = {
            'success': True,
            'total_records': total_records,
            'total_deletable': total_deletable,
            'table_stats': stats,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Database stats requested: {total_records:,} total records, {total_deletable:,} deletable")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/admin/cleanup/recommendations", methods=['GET'])
@rate_limit(max_requests=10)
def get_cleanup_recs():
    """Get intelligent cleanup recommendations based on database analysis"""
    try:
        recommendations = get_cleanup_recommendations()
        
        if 'error' in recommendations:
            return jsonify({'success': False, 'error': recommendations['error']}), 500
        
        response = {
            'success': True,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Cleanup recommendations generated: {recommendations['recommended_action']}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating cleanup recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/admin/cleanup/dry-run", methods=['POST'])
@rate_limit(max_requests=5)  # Very limited for resource-intensive operations
def cleanup_dry_run():
    """Perform a dry run cleanup to see what would be deleted without actually deleting"""
    try:
        logger.info("Starting cleanup dry run...")
        result = run_cleanup(dry_run=True)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500
        
        response = {
            'success': True,
            'dry_run': True,
            'result': result,
            'message': f"Dry run completed. Would delete {result['total_deleted']:,} records"
        }
        
        logger.info(f"Cleanup dry run completed: {result['total_deleted']:,} records would be deleted")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in cleanup dry run: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/admin/cleanup/execute", methods=['POST'])
@rate_limit(max_requests=3)  # Extremely limited for actual cleanup
def execute_cleanup():
    """Execute actual database cleanup - USE WITH CAUTION!"""
    try:
        # Get confirmation parameter
        confirm = request.json.get('confirm') if request.is_json else False
        
        if not confirm:
            return jsonify({
                'success': False, 
                'error': 'Cleanup requires explicit confirmation. Send {"confirm": true} in request body.'
            }), 400
        
        logger.warning(" EXECUTING LIVE DATABASE CLEANUP ")
        result = run_cleanup(dry_run=False)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500
        
        response = {
            'success': True,
            'dry_run': False,
            'result': result,
            'message': f"Cleanup completed successfully. Deleted {result['total_deleted']:,} records in {result['duration']:.2f} seconds"
        }
        
        logger.warning(f" LIVE CLEANUP COMPLETED: {result['total_deleted']:,} records deleted in {result['duration']:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in live cleanup execution: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/admin/cleanup/scheduler/start", methods=['POST'])
@rate_limit(max_requests=5)
def start_cleanup_scheduler():
    """Start the automated cleanup scheduler"""
    try:
        start_automated_cleanup()
        
        response = {
            'success': True,
            'message': 'Automated cleanup scheduler started',
            'schedule': 'Every 7 days at 3:00 AM'
        }
        
        logger.info(" Automated cleanup scheduler started")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error starting cleanup scheduler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/admin/cleanup/scheduler/stop", methods=['POST'])
@rate_limit(max_requests=5)
def stop_cleanup_scheduler():
    """Stop the automated cleanup scheduler"""
    try:
        stop_automated_cleanup()
        
        response = {
            'success': True,
            'message': 'Automated cleanup scheduler stopped'
        }
        
        logger.info(" Automated cleanup scheduler stopped")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error stopping cleanup scheduler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
