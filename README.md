# 🍽️ Store Monitoring

## 📌 Description
This project implements backend APIs to monitor restaurant uptime and downtime relative to their business hours.  
It processes **poll data (active/inactive status)**, **business hours**, and **time zone information** to generate **uptime/downtime reports** for store owners.  

The system works with hourly updating data sources and ensures reports reflect **accurate, interpolated results** even with incomplete polling data.  

---

## ✨ Features
- **Data ingestion**: Reads poll data, business hours, and timezone info from CSVs.  
- **Database storage**: Uses PostgreSQL (or SQLite for local testing).  
- **Timezone handling**: Converts UTC timestamps into each store’s local time.  
- **Business hour filtering**: Calculates uptime/downtime only within store business hours (defaults to 24×7 if missing).  
- **Interpolation logic**: Extends uptime/downtime status between polls.  
- **Dynamic reports**: Computes uptime and downtime for:
  - Last hour
  - Last day
  - Last week  
- **APIs**:
  - `/trigger_report` → Starts report generation asynchronously.  
  - `/get_report` → Returns report status or completed report in CSV.  

---

## ⚙️ Requirements
- Python **3.9+**
- pip (Python package manager)
- PostgreSQL (recommended) or SQLite (for testing)

### Python Libraries
- **Flask** or **FastAPI** → REST API framework  
- **SQLAlchemy** → ORM for DB integration  
- **Pandas** → Data processing and CSV handling  
- **pytz / zoneinfo** → Timezone conversion  
- **Celery / Threading** → Background job execution  

---

## 🛠️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/nsvsaikrishna0312/nallajarla_19-08-2025.git
cd nallajarla_19-08-2025

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
