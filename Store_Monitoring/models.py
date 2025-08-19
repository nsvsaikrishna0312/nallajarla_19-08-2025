from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class StoreStatus(db.Model):
    __tablename__ = "store_status"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(50), index=True, nullable=False)
    timestamp_utc = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class BusinessHours(db.Model):
    __tablename__ = "business_hours"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(50), index=True, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon, 6=Sun
    start_time_local = db.Column(db.Time, nullable=False)
    end_time_local = db.Column(db.Time, nullable=False)

class StoreTimezone(db.Model):
    __tablename__ = "store_timezones"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(50), index=True, nullable=False)
    timezone_str = db.Column(db.String(50), nullable=False)
