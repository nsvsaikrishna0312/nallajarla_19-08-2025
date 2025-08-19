from flask import Blueprint

bp = Blueprint("data", __name__)

from flask import request, jsonify
from services import StoreMonitoringService

@bp.route("/load_data", methods=["POST"])
def load_data():
    try:
        data = request.get_json(force=True, silent=True) or {}
        reset = data.get("reset", False)

        service = StoreMonitoringService()
        csv_folder = "data"

        service.load_data_from_csvs(csv_folder, reset=reset)

        return jsonify({
            "status": "success",
            "reset": reset,
            "message": f"Data {'reloaded' if reset else 'appended'} from CSVs"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

