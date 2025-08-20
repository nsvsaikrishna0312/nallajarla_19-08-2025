"""
Test script for Flask Store Monitoring API
This script demonstrates the complete workflow of the system
"""

import requests
import time
import json
from datetime import datetime, timedelta, timezone
import random
import os

# Configuration
BASE_URL = "http://127.0.0.1:5000/"
HEADERS = {'Content-Type': 'application/json'}
STORE_IDS = ["0001", "0002", "0003"]
STATUSES = ["active", "inactive"]


def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def test_load_data():
    """Test data loading endpoint"""
    print("\n Testing data loading...")
    try:
        payload = {"csv_folder": "data"}
        response = requests.post(f"{BASE_URL}/load_data", json=payload, headers=HEADERS)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f" Data loading failed: {e}")
        return False


def test_ingest_streaming(num_events=10, delay=1):
    """Test streaming ingestion with UTC formatted timestamps"""
    print("\n Testing streaming ingestion...")

    for i in range(num_events):
        # Generate UTC timestamp in required format
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")

        payload = {
            "store_id": random.choice(STORE_IDS),
            "status": random.choice(["active", "inactive"]),
            "timestamp_utc": timestamp
        }

        try:
            response = requests.post(f"{BASE_URL}/ingest", json=payload, headers=HEADERS)
            if response.status_code == 200:
                print(f" Event {i+1} ingested: {payload}")
            else:
                print(f" Failed {response.status_code}: {response.text}")
        except Exception as e:
            print(f" Error during ingestion: {e}")

        time.sleep(delay)

def test_trigger_report():
    """Test report generation trigger"""
    print("\n Testing report generation trigger...")
    try:
        response = requests.post(f"{BASE_URL}/trigger_report")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200 and 'report_id' in data:
            return data['report_id']
        return None
    except Exception as e:
        print(f" Report trigger failed: {e}")
        return None


def test_get_report(report_id):
    """Test report status checking and download"""
    print(f"\n Testing report status for ID: {report_id}")

    max_attempts = 50  # Maximum wait time: 30 attempts * 10 seconds = 5 minutes
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/get_report?report_id={report_id}")
            print(f"Attempt {attempt + 1}: Status {response.status_code}")

            if response.status_code == 200:
                # Check if it's a JSON response (still running) or file download (complete)
                content_type = response.headers.get('content-type', '')

                if 'application/json' in content_type:
                    data = response.json()
                    print(f"Report status: {data.get('status', 'Unknown')}")

                    if data.get('status') == 'Running':
                        print(" Report still running, waiting...")
                        time.sleep(10)
                        attempt += 1
                        continue
                    else:
                        print(f"❌ Unexpected status: {data}")
                        return False

                elif 'text/csv' in content_type:
                    print(" Report completed! Downloading CSV...")

                    # Save the CSV file
                    filename = f"downloaded_report_{report_id}.csv"
                    with open(filename, 'wb') as f:
                        f.write(response.content)

                    print(f" Report saved as: {filename}")

                    # Show first few lines of the CSV
                    with open(filename, 'r') as f:
                        lines = f.readlines()[:6]  # Header + first 5 rows
                        print("\n Sample report data:")
                        for line in lines:
                            print(line.strip())

                    return True
                else:
                    print(f" Unexpected content type: {content_type}")
                    return False

            elif response.status_code == 404:
                print(" Report not found")
                return False

            elif response.status_code == 500:
                data = response.json()
                print(f" Report generation failed: {data.get('error', 'Unknown error')}")
                return False

            else:
                print(f" Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f" Error checking report: {e}")
            return False

    print(" Report generation timed out")
    return False


def test_list_reports():
    """Test listing all reports"""
    print("\n Testing report listing...")
    try:
        response = requests.get(f"{BASE_URL}/reports")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f" Report listing failed: {e}")
        return False


def main():
    
    if not test_health_check():
        print("\n Server is not responding. Please start the Flask app first:")
        print("   python main.py")
        return
    #
    # Test data loading (optional - if CSV files exist)
    # if os.path.exists("data"):
    #     test_load_data()
    # else:
    #     print("\n  No data folder found. Please run data_loader.py first or manually create CSV files.")

    # Test report generation
    report_id = test_trigger_report()
    if not report_id:
        print("\n Failed to trigger report generation")
        return

    # Test report status checking and download
    if test_get_report(report_id):
        print("\n Report generation and download successful!")
    else:
        print("\n Report generation or download failed")

    # Test report listing
    # test_list_reports()

    print("\n" + "=" * 50)
    print(" Testing completed!")
    test_ingest_streaming(num_events=15, delay=0.5)



if __name__ == "__main__":
    main()
