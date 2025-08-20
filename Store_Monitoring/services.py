import os
import pytz
import pandas as pd
from datetime import datetime, timedelta, time

from models import db, StoreStatus, BusinessHours, StoreTimezone
from config import logger
report_status = {}

class StoreMonitoringService:
    def __init__(self):
        pass

    def load_data_from_csvs(self, csv_folder: str, reset: bool = False):
        try:
            if reset:
                logger.info("Reset mode ON: Clearing existing data...")
                db.session.query(StoreStatus).delete()
                db.session.query(BusinessHours).delete()
                db.session.query(StoreTimezone).delete()

            status_file = os.path.join(csv_folder, 'store_status.csv')
            if os.path.exists(status_file):
                status_df = pd.read_csv(status_file)
                status_df['timestamp_utc'] = pd.to_datetime(status_df['timestamp_utc'])

                inserted = 0
                for _, row in status_df.iterrows():
                    exists = StoreStatus.query.filter_by(
                        store_id=str(row['store_id']),
                        timestamp_utc=row['timestamp_utc'],
                        status=row['status']
                    ).first()

                    if not exists:
                        store_status = StoreStatus(
                            store_id=str(row['store_id']),
                            timestamp_utc=row['timestamp_utc'],
                            status=row['status']
                        )
                        db.session.add(store_status)
                        inserted += 1
                        logger.info(f"Inserted {inserted} new store status records")

                logger.info(f"Inserted {inserted} new store status records")

            hours_file = os.path.join(csv_folder, 'menu_hours.csv')
            if os.path.exists(hours_file):
                hours_df = pd.read_csv(hours_file)
                inserted = 0
                for _, row in hours_df.iterrows():
                    start_time = datetime.strptime(row['start_time_local'], '%H:%M:%S').time()
                    end_time = datetime.strptime(row['end_time_local'], '%H:%M:%S').time()

                    exists = BusinessHours.query.filter_by(
                        store_id=str(row['store_id']),
                        day_of_week=int(row['dayOfWeek']),
                        start_time_local=start_time,
                        end_time_local=end_time
                    ).first()

                    if not exists:
                        business_hour = BusinessHours(
                            store_id=str(row['store_id']),
                            day_of_week=int(row['dayOfWeek']),
                            start_time_local=start_time,
                            end_time_local=end_time
                        )
                        db.session.add(business_hour)
                        inserted += 1

                logger.info(f"Inserted {inserted} new business hours records")
            else:
                logger.warning("Business hours CSV not found, will use 24/7 default")

            tz_file = os.path.join(csv_folder, 'timezones.csv')
            if os.path.exists(tz_file):
                tz_df = pd.read_csv(tz_file)
                inserted = 0
                for _, row in tz_df.iterrows():
                    exists = StoreTimezone.query.filter_by(
                        store_id=str(row['store_id'])
                    ).first()

                    if not exists:
                        store_tz = StoreTimezone(
                            store_id=str(row['store_id']),
                            timezone_str=row['timezone_str']
                        )
                        db.session.add(store_tz)
                        inserted += 1

                logger.info(f"Inserted {inserted} new timezone records")
            else:
                logger.warning("Timezone CSV not found, will use America/Chicago default")

            db.session.commit()
            logger.info("CSV load completed successfully")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error loading data: {e}")
            raise

    def get_store_timezone(self, store_id: str) -> str:
        tz_record = StoreTimezone.query.filter_by(store_id=store_id).first()
        return tz_record.timezone_str if tz_record else "America/Chicago"

    def get_business_hours(self, store_id: str) -> list[tuple]:
        hours = BusinessHours.query.filter_by(store_id=store_id).all()

        if not hours:
            return [(i, time(0, 0, 0), time(23, 59, 59)) for i in range(7)]

        return [(h.day_of_week, h.start_time_local, h.end_time_local) for h in hours]

    def is_within_business_hours(self, timestamp: datetime, store_id: str) -> bool:
        store_tz = pytz.timezone(self.get_store_timezone(store_id))

        if timestamp.tzinfo is None:
            timestamp = pytz.UTC.localize(timestamp)

        local_time = timestamp.astimezone(store_tz)
        business_hours = self.get_business_hours(store_id)
        day_of_week = local_time.weekday()  # 0=Monday, 6=Sunday
        current_time = local_time.time()

        for day, start_time, end_time in business_hours:
            if day == day_of_week:
                if start_time <= end_time:
                    if start_time <= current_time <= end_time:
                        return True
                else:
                    if current_time >= start_time or current_time <= end_time:
                        return True

        return False

    def get_business_hours_in_period(self, store_id: str, start_datetime: datetime, end_datetime: datetime) -> float:
        store_tz = pytz.timezone(self.get_store_timezone(store_id))
        business_hours = self.get_business_hours(store_id)

        if start_datetime.tzinfo is None:
            start_datetime = pytz.UTC.localize(start_datetime)
        if end_datetime.tzinfo is None:
            end_datetime = pytz.UTC.localize(end_datetime)

        local_start = start_datetime.astimezone(store_tz)
        local_end = end_datetime.astimezone(store_tz)

        total_hours = 0.0
        current = local_start.replace(hour=0, minute=0, second=0, microsecond=0)

        while current.date() <= local_end.date():
            day_of_week = current.weekday()

            day_business_hours = [(start, end) for day, start, end in business_hours if day == day_of_week]

            for start_time, end_time in day_business_hours:

                day_start = current.replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=start_time.second
                )
                day_end = current.replace(
                    hour=end_time.hour,
                    minute=end_time.minute,
                    second=end_time.second
                )

                if end_time < start_time:
                    day_end += timedelta(days=1)

                period_start = max(day_start, local_start)
                period_end = min(day_end, local_end)

                if period_start < period_end:
                    duration = (period_end - period_start).total_seconds() / 3600
                    total_hours += duration

            current += timedelta(days=1)

        return total_hours

    def calculate_uptime_downtime(self, store_id: str, start_time: datetime, end_time: datetime) -> tuple[float, float]:
        buffer_time = timedelta(hours=2)
        query_start = start_time - buffer_time

        status_data = StoreStatus.query.filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= query_start,
            StoreStatus.timestamp_utc <= end_time
        ).order_by(StoreStatus.timestamp_utc).all()

        if not status_data:
            business_hours_duration = self.get_business_hours_in_period(store_id, start_time, end_time)
            return business_hours_duration, 0.0

        total_uptime = 0.0
        total_downtime = 0.0

        for i in range(len(status_data)):
            current_obs = status_data[i]
            current_time = current_obs.timestamp_utc
            is_active = current_obs.status == 'active'

            if current_time.tzinfo is None:
                current_time = pytz.UTC.localize(current_time)

            if current_time < start_time:
                continue

            if i + 1 < len(status_data):
                next_time = status_data[i + 1].timestamp_utc
                if next_time.tzinfo is None:
                    next_time = pytz.UTC.localize(next_time)
                interval_end = min(next_time, end_time)
            else:
                interval_end = end_time

            if interval_end.tzinfo is None:
                interval_end = pytz.UTC.localize(interval_end)

            if current_time < interval_end:
                interval_start = max(current_time, start_time)
                duration = self.get_business_hours_in_period(store_id, interval_start, interval_end)

                if is_active:
                    total_uptime += duration
                else:
                    total_downtime += duration

        return total_uptime, total_downtime

    def generate_report_background(self, report_id):
        try:
            from app import create_app
            app = create_app()

            with app.app_context():
                logger.info(f"Starting background report generation: {report_id}")

                # Fetch max timestamp
                max_timestamp_result = db.session.query(StoreStatus.timestamp_utc).order_by(
                    StoreStatus.timestamp_utc.desc()
                ).first()

                if not max_timestamp_result:
                    raise Exception("No data found in store_status table")

                current_time = max_timestamp_result[0]
                if current_time.tzinfo is None:
                    current_time = pytz.UTC.localize(current_time)

                one_hour_ago = current_time - timedelta(hours=1)
                one_day_ago = current_time - timedelta(days=1)
                one_week_ago = current_time - timedelta(weeks=1)

                store_ids = [row[0] for row in db.session.query(StoreStatus.store_id).distinct().all()]

                results = []

                logger.info(f"Processing {len(store_ids)} stores for report {report_id}")

                for idx, store_id in enumerate(store_ids, 1):
                    try:
                        uptime_hour, downtime_hour = self.calculate_uptime_downtime(store_id, one_hour_ago,
                                                                                    current_time)
                        uptime_day, downtime_day = self.calculate_uptime_downtime(store_id, one_day_ago,
                                                                                  current_time)
                        uptime_week, downtime_week = self.calculate_uptime_downtime(store_id, one_week_ago,
                                                                                    current_time)

                        results.append({
                            'store_id': store_id,
                            'uptime_last_hour': round(uptime_hour * 60, 2),  # minutes
                            'uptime_last_day': round(uptime_day, 2),
                            'uptime_last_week': round(uptime_week, 2),
                            'downtime_last_hour': round(downtime_hour * 60, 2),
                            'downtime_last_day': round(downtime_day, 2),
                            'downtime_last_week': round(downtime_week, 2)
                        })

                        if idx % 100 == 0:
                            logger.info(f"Processed {idx}/{len(store_ids)} stores")

                    except Exception as e:
                        logger.error(f"Error processing store {store_id}: {e}")
                        continue

                if results:
                    df = pd.DataFrame(results)
                    report_dir = "reports"
                    os.makedirs(report_dir, exist_ok=True)
                    report_path = os.path.join(report_dir, f"report_{report_id}.csv")
                    df.to_csv(report_path, index=False)

                    report_status[report_id] = {
                        "status": "Complete",
                        "file_path": report_path,
                        "completed_at": datetime.now(pytz.UTC).isoformat(),
                        "total_stores": len(results)
                    }
                    logger.info(f"Report {report_id} generated successfully ({len(results)} stores)")
                else:
                    raise Exception("No valid results generated")

        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            report_status[report_id] = {
                "status": "Failed",
                "error": str(e),
                "completed_at": datetime.now(pytz.UTC).isoformat()
            }

def run_report_in_background(report_id):
    service = StoreMonitoringService()
    thread = Thread(target=service.generate_report_background, args=(report_id,))
    thread.start()
    logger.info(f"Report generation thread started for {report_id}")
