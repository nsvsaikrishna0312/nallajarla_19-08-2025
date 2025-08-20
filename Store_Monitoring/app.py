from flask import Flask
from models import db, StoreStatus, StoreTimezone, BusinessHours
from services import StoreMonitoringService
from routes import health_routes, ingest_routes, report_routes, data_routes
from utils.errors import register_error_handlers
from config import DB_URI, logger
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

import os

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "supersecretkey"  # Required by Flask-Admin


    db.init_app(app)

    with app.app_context():
        db.create_all()

        if StoreStatus.query.count() == 0 and StoreTimezone.query.count() == 0:
            csv_folder = "data"
            if os.path.exists(csv_folder) and any(f.endswith(".csv") for f in os.listdir(csv_folder)):
                try:
                    logger.info("Loading initial data from CSV files...")
                    StoreMonitoringService().load_data_from_csvs(csv_folder)
                except Exception as e:
                    logger.warning(f"Could not load CSV data on startup: {e}")
            else:
                logger.info("No CSV files found, skipping bootstrap load")
        else:
            logger.info("Database already has data, skipping CSV bootstrap load")

    admin = Admin(app, name="Store Monitoring Admin", template_mode="bootstrap3")
    admin.add_view(ModelView(StoreStatus, db.session))
    admin.add_view(ModelView(StoreTimezone, db.session))
    admin.add_view(ModelView(BusinessHours,db.session))

    app.register_blueprint(health_routes.bp)
    app.register_blueprint(ingest_routes.bp)
    app.register_blueprint(report_routes.bp)
    app.register_blueprint(data_routes.bp)

    register_error_handlers(app)

    return app

if __name__ == "__main__":
    try:
        app = create_app()
        print(" Starting Flask app on http://127.0.0.1:5000 ...")
        app.run(debug=True, host="127.0.0.1", port=5000)
    except Exception as e:
        import traceback

        print(" Flask app failed to start!")
        traceback.print_exc()

