import pymysql
import datetime
import logging
from contextlib import contextmanager
from backend.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, MAX_DB_CONNECTIONS

logger = logging.getLogger(__name__)

# Create connection pool for better performance
connection_pool = None

def initialize_connection_pool():
    """Initialize the database connection pool"""
    global connection_pool
    try:
        connection_pool = pymysql.pooling.ConnectionPool(
            pool_name='telemetry_pool',
            pool_size=MAX_DB_CONNECTIONS,
            pool_reset_session=True,
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        logger.info(f"Database connection pool initialized with {MAX_DB_CONNECTIONS} connections")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        if connection_pool is None:
            initialize_connection_pool()
        conn = connection_pool.get_connection()
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def connect_db():
    """Legacy function for backwards compatibility"""
    if connection_pool is None:
        initialize_connection_pool()
    return connection_pool.get_connection()

def ts(rows):
    for r in rows:
        if isinstance(r.get("timestamp"), datetime.datetime):
            r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return rows

BATTERY = """
SELECT id, timestamp,
       Battery_Volt               AS battery_volt,
       Battery_Current            AS battery_current,
       Battery_Cell_Low_Volt      AS battery_cell_low_volt,
       Battery_Cell_High_Volt     AS battery_cell_high_volt,
       Battery_Cell_Average_Volt  AS battery_cell_average_volt,
       Battery_Cell_Low_Temp      AS battery_cell_low_temp,
       Battery_Cell_High_Temp     AS battery_cell_high_temp,
       Battery_Cell_Average_Temp  AS battery_cell_average_temp,
       Battery_Cell_High_Temp_ID  AS battery_cell_high_temp_ID,
       Battery_Cell_Low_Temp_ID   AS battery_cell_low_temp_ID
FROM `Battery Data Table`
WHERE Battery_Volt <> 0           -- ← skip zero rows
ORDER BY id DESC
LIMIT %s;
"""

MOTOR = """
SELECT id, timestamp,
       Motor_Current        AS motor_current,
       Motor_Temp           AS motor_temp,
       Motor_Controller_Temp AS motor_controller_temp
FROM `Motor Data Table`
WHERE Motor_Temp <> 0 OR Motor_Current <> 0
ORDER BY id DESC
LIMIT %s;
"""

MPPT = """
SELECT id, timestamp,
       MPPT1_Watt      AS MPPT1_watt,
       MPPT2_Watt      AS MPPT2_watt,
       MPPT3_Watt      AS MPPT3_watt,
       MPPT_Total_Watt AS MPPT_total_watt
FROM `MPPT Data Table`
WHERE MPPT_Total_Watt <> 0
ORDER BY id DESC
LIMIT %s;
"""

VEHICLE = """
SELECT id, timestamp,
       Velocity           AS velocity,
       Distance_Travelled AS distance_travelled
FROM `Vehicle Data Table`
WHERE Velocity <> 0
ORDER BY id DESC
LIMIT %s;
"""

def fetch_all_data(limit=20):
    """Fetch all telemetry data with improved error handling"""
    out = {"battery_data": [], "motor_data": [], "mppt_data": [], "vehicle_data": []}
    
    # Validate limit parameter
    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        logger.warning(f"Invalid limit parameter: {limit}, using default 20")
        limit = 20
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                # Execute queries with error handling for each
                try:
                    c.execute(BATTERY, (limit,))
                    out["battery_data"] = ts(c.fetchall())
                except Exception as e:
                    logger.error(f"Error fetching battery data: {e}")
                
                try:
                    c.execute(MOTOR, (limit,))
                    out["motor_data"] = ts(c.fetchall())
                except Exception as e:
                    logger.error(f"Error fetching motor data: {e}")
                
                try:
                    c.execute(MPPT, (limit,))
                    out["mppt_data"] = ts(c.fetchall())
                except Exception as e:
                    logger.error(f"Error fetching MPPT data: {e}")
                
                try:
                    c.execute(VEHICLE, (limit,))
                    out["vehicle_data"] = ts(c.fetchall())
                except Exception as e:
                    logger.error(f"Error fetching vehicle data: {e}")
                    
        logger.debug(f"Successfully fetched data with limit {limit}")
        
    except Exception as e:
        logger.error(f"Database connection error in fetch_all_data: {e}")
        # Return empty data structure instead of crashing
    
    return out

def validate_table_name(table_name):
    """Validate table names to prevent injection"""
    allowed_tables = {
        'battery': '`Battery Data Table`',
        'motor': '`Motor Data Table`',
        'mppt': '`MPPT Data Table`',
        'vehicle': '`Vehicle Data Table`'
    }
    return allowed_tables.get(table_name)

def health_check():
    """Check database connectivity for health endpoint"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1")
                return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
