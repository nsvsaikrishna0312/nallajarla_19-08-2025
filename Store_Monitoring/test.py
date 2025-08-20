"""
Pytest-based test cases for Flask Store Monitoring API
"""

import pytest
import requests
import time
import json
from datetime import datetime, timezone
import random

# Configuration
BASE_URL = "http://127.0.0.1:5000"
HEADERS = {'Content-Type': 'application/json'}
STORE_IDS = ["0001", "0002", "0003"]


@pytest.fixture(scope="session")
def report_id():
    response = requests.post(f"{BASE_URL}/trigger_report")
    assert response.status_code == 200, "Failed to trigger report"
    data = response.json()
    assert "report_id" in data, "Response missing report_id"
    return data["report_id"]


def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"].lower() in ["ok", "healthy"]


def test_ingest_streaming():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")

    payload = {
        "store_id": random.choice(STORE_IDS),
        "status": random.choice(["active", "inactive"]),
        "timestamp_utc": timestamp
    }

    response = requests.post(f"{BASE_URL}/ingest", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data.get("message", "").lower().find("ingested") != -1


def test_trigger_report():
    response = requests.post(f"{BASE_URL}/trigger_report")
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data


def test_get_report(report_id):
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/get_report?report_id={report_id}")

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                assert data.get("status") in ["Running", "Completed", "Failed"]
                if data.get("status") == "Running":
                    time.sleep(5)
                    continue
                elif data.get("status") == "Completed":
                    pytest.skip("Report marked completed but not downloadable yet")
            elif "text/csv" in content_type:
                # CSV report is ready
                assert response.content.startswith(b"store_id")  # header check
                return
        elif response.status_code in (404, 500):
            pytest.fail(f"Report failed with status {response.status_code}")

    pytest.fail("Report generation timed out")


def test_list_reports():
    response = requests.get(f"{BASE_URL}/reports")
    assert response.status_code == 200
    data = response.json()
