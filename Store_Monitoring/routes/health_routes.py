from datetime import datetime
from flask import Blueprint, jsonify
from models import StoreStatus

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health_check():
    try:
        store_count = StoreStatus.query.count()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stores_in_db": store_count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
