from flask import Blueprint, request, jsonify, send_file
import os, uuid
from datetime import datetime
import threading
from services import StoreMonitoringService, report_status

bp = Blueprint("report", __name__)

@bp.route("/trigger_report", methods=["POST"])
def trigger_report():
    try:
        report_id = str(uuid.uuid4())
        report_status[report_id] = {"status": "Running", "started_at": datetime.now().isoformat()}
        service = StoreMonitoringService()

        thread = threading.Thread(
            target=service.generate_report_background,  # call method on instance
            args=(report_id,),
        )
        thread.daemon = True
        thread.start()

        return jsonify({"report_id": report_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/get_report", methods=["GET"])
def get_report():
    report_id = request.args.get("report_id")

    if not report_id:
        return jsonify({"error": "report_id parameter is required"}), 400
    if report_id not in report_status:
        return jsonify({"error": "Report not found"}), 404

    status_info = report_status[report_id]

    if status_info["status"] == "Running":
        return jsonify({"status": "Running"}), 200
    elif status_info["status"] == "Complete":
        if os.path.exists(status_info["file_path"]):
            return send_file(
                status_info["file_path"],
                as_attachment=True,
                download_name=f"store_monitoring_report_{report_id}.csv",
                mimetype="text/csv"
            )
        return jsonify({"error": "Report file not found"}), 404
    elif status_info["status"] == "Failed":
        return jsonify({"error": status_info.get("error", "Unknown error")}), 500

    return jsonify({"error": "Unknown report status"}), 500

@bp.route("/reports", methods=["GET"])
def list_reports():
    return jsonify({"reports": report_status}), 200
