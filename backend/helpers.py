import pymysql, datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def connect_db():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, cursorclass=pymysql.cursors.DictCursor
    )

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
    out = {"battery_data": [], "motor_data": [], "mppt_data": [], "vehicle_data": []}
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as c:
            c.execute(BATTERY, (limit,)); out["battery_data"] = ts(c.fetchall())
            c.execute(MOTOR,   (limit,)); out["motor_data"]   = ts(c.fetchall())
            c.execute(MPPT,    (limit,)); out["mppt_data"]    = ts(c.fetchall())
            c.execute(VEHICLE, (limit,)); out["vehicle_data"] = ts(c.fetchall())
    except Exception as e:
        print("DB Error:", e)
    finally:
        if conn and conn.open: conn.close()
    return out
