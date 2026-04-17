# Deployment Guide - Cloud FinOps Intelligence Platform

This document outlines the steps to deploy the FinOps platform in both development and production environments.

## Prerequisites
- **Docker Desktop** (Mac/Windows) or **Docker Engine + Compose** (Linux)
- **8GB RAM** recommended (TimescaleDB + Python ML models consume significant memory)
- **Groq API key** (Obtain for free at [console.groq.com](https://console.groq.com/))

---

## 🏗 Quick Start (Local Development)

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 2. Infrastructure
Bring up the database:
```bash
docker compose up -d timescaledb
# Wait ~15 seconds for the database to be healthy
```

### 3. Data Ingestion & ML Pipeline
Run the following steps in sequence to populate the platform:
```bash
# Install dependencies
pip install -r ingestion/requirements.txt -r detection/requirements.txt -r forecasting/requirements.txt

# Run pipeline
python ingestion/main.py --mode synthetic --start 2024-01-01 --end 2026-12-31
python normalization/pipeline.py
python storage/runner.py
python features/main.py --start 2024-01-01 --end 2026-12-31
python detection/main.py --start 2024-01-01 --end 2026-12-31
python forecasting/run_forecasting.py --start 2024-01-01 --end 2026-12-31
python attribution/main.py --start 2024-01-01 --end 2026-12-31
python alerting/main.py --start 2024-01-01 --end 2026-12-31
```

### 4. Application
```bash
# Start API
uvicorn api.main:app --reload --port 8000

# Start Frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

---

## 🚢 Production Deployment (All-in-one)

The production stack brings up TimescaleDB, the FastAPI backend, and the React frontend (served via Nginx) in a single command.

### 1. Production Config
```bash
cp .env.example .env.production
# Edit .env.production:
# - Set secure passwords for TIMESCALE_PASSWORD
# - Set your GROQ_API_KEY
# - Update VITE_API_URL to your public domain/IP
```

### 2. Orchestration
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 3. Initial Data Load (Production)
Since the production database volume is empty, run the ingestion inside the container:
```bash
docker exec finops_api_prod python ingestion/main.py --mode synthetic --start 2024-01-01 --end 2026-12-31
# Repeat for other pipeline steps as needed using 'docker exec'
```

---

## 🌩 Hybrid Cloud Deployment (Render + Vercel)

This is the recommended **Free Tier** path. It uses the cloud for the dashboard but uses your local machine's RAM for the heavy ML processing to avoid crashes on free servers.

### 1. Infrastructure Setup (Cloud)

#### A. Database (Render)
1. Log in to [Render.com](https://render.com) and create a **PostgreSQL** instance.
2. In the Render Dashboard, go to the **Query** tab (or connect via `psql` locally) and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   ```
3. Copy the **External Database URL**.

#### B. API (Render)
1. Create a **Web Service** on Render pointing to your GitHub repository.
2. **Environment Variables**:
   - `DATABASE_URL`: (Paste your External DB URL from above).
   - `GROQ_API_KEY`: (Your key).
   - `ALLOWED_ORIGINS`: `https://your-app.vercel.app` (Update this after Step C).
3. **Start Command**: `export PYTHONPATH=$PYTHONPATH:. && uvicorn api.main:app --host 0.0.0.0 --port $PORT`

#### C. Frontend (Vercel)
1. Import your repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. **Environment Variable**: `VITE_API_URL` = your Render API URL.
4. Once deployed, copy your `.vercel.app` URL and add it to Render's `ALLOWED_ORIGINS`.

---

### 2. The Hybrid Data Pipeline (Local machine -> Cloud DB)

Since Render's free tier has limited RAM, you should run the "heavy" ML parts on your computer. They will process the data locally and push the results directly to your Render database.

#### Step 1: Sync the Schema
```bash
# Set your Remote DB URL
# Windows
$env:DATABASE_URL="postgres://user:pass@host/db"
# Mac/Linux
export DATABASE_URL="postgres://user:pass@host/db"

# Create the tables in the cloud
python scripts/setup_remote_db.py
```

#### Step 2: Run the ML Engines locally
Run these commands one by one. They will connect to Render and populate your cloud dashboard with data:
```bash
# 1. Ingest Synthetic Data
python ingestion/main.py --mode synthetic --start 2024-01-01 --end 2026-12-31

# 2. Normalize & Store
python normalization/pipeline.py
python storage/runner.py

# 3. Generate Features
python features/main.py --start 2024-01-01 --end 2026-12-31

# 4. Detect Anomalies (ML)
python detection/main.py --start 2024-01-01 --end 2026-12-31

# 5. Generate Forecasts (Prophet ML)
python forecasting/run_forecasting.py --start 2024-01-01 --end 2026-12-31

# 6. Attribution & Alerts
python attribution/main.py --start 2024-01-01 --end 2026-12-31
python alerting/main.py --start 2024-01-01 --end 2026-12-31
```

---

## 🔍 Verification & Health
- **API Health**: `curl http://localhost:8000/health` (should return `db_connected: true`)
- **Dashboard**: Open `http://localhost:3000` in your browser.
- **SPA Routing**: Directly navitaging to `/anomalies` should work (provided by Nginx fallback).

## 🛑 Stopping & Maintenance
```bash
# Stop containers
docker compose -f docker-compose.prod.yml down

# Stop and delete ALL data volumes (destructive!)
docker compose -f docker-compose.prod.yml down -v
```
