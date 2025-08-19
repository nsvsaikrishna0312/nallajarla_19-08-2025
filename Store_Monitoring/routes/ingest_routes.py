from flask import Blueprint, request, jsonify
import datetime
from models import db, StoreStatus

bp = Blueprint("ingest", __name__)

@bp.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json()
        ts = datetime.datetime.strptime(data["timestamp_utc"], "%Y-%m-%d %H:%M:%S.%f UTC")
        new_record = StoreStatus(
            store_id=data["store_id"],
            status=data["status"],
            timestamp_utc=ts
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"message": "Ingested successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
