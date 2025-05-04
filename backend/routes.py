from flask import Blueprint, render_template, request, jsonify, make_response
from helpers import fetch_all_data

main = Blueprint('main', __name__)
routes = Blueprint('routes', __name__)

@routes.route("/")
def index():
    return render_template("index.html")




@main.route("/data")
def get_data():
    limit = request.args.get("limit", default=20, type=int)
    data = fetch_all_data(limit=limit)
    return jsonify(data)

@main.route("/export_csv")
def export_csv():
    data_rows = fetch_all_data(limit=20)
    csv_lines = ["Table,ID,Timestamp,Value1,Value2\n"]

    for row in data_rows["battery_data"]:
        csv_lines.append(f"Battery,{row['id']},{row['timestamp']},{row['battery_volt']},{row['battery_current']}\n")

    for row in data_rows["motor_data"]:
        csv_lines.append(f"Motor,{row['id']},{row['timestamp']},{row['motor_current']},{row['motor_temp']}\n")

    resp = make_response("".join(csv_lines))
    resp.headers["Content-Disposition"] = "attachment; filename=hust_data_export.csv"
    resp.mimetype = "text/csv"
    return resp
