# InsightCart — Project Startup Guide

This document explains how to start the InsightCart application locally.

## 1. Project Structure

```text
InsightCart/
├── backend/
│   ├── scripts/
│   │   ├── app/
│   │   ├── loader.py
│   │   └── load_data.py
│   └── requirements.txt
├── frontend/
│   └── frontend/
├── sales.csv
├── customers.csv
├── products.csv
├── dates.csv
├── .env
└── .gitignore
```

**Stack:** React + Vite + Tailwind CSS + Recharts, FastAPI, PostgreSQL, Pandas, SQLAlchemy.

## 2. Prerequisites

Install:
- Python 3
- Node.js and npm
- PostgreSQL
- Git

The current backend expects PostgreSQL on port `5433`.

## 3. Database Setup

Start PostgreSQL first. The expected database is `insightcart` with schema `retail`.

Main tables:

```text
retail.fact_sales
retail.dim_customers
retail.dim_products
retail.dim_date
```

The backend reads the connection string from `.env`:

```env
DATABASE_URL=postgresql://postgres:<YOUR_PASSWORD>@localhost:5433/insightcart
```

Never commit the real `.env` or database password.

## 4. Backend Setup

From the project root:

```powershell
cd "C:\Users\Siddhant\OneDrive\Desktop\InsightCart\InsightCart\backend\scripts"
```

Create a virtual environment if needed:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r ..\requirements.txt
```

## 5. Start the FastAPI Backend

From `backend\scripts`:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

Keep this terminal running.

## 6. Verify the Backend

In another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/dashboard-summary
```

Available endpoints:

```text
/api/dashboard-summary
/api/trends
/api/categories
/api/products
/api/customers
/api/data-quality
/api/reconciliation
/api/exceptions
```

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/data-quality
Invoke-RestMethod http://127.0.0.1:8000/api/exceptions
```

## 7. Start the Frontend

Open another PowerShell window:

```powershell
cd "C:\Users\Siddhant\OneDrive\Desktop\InsightCart\InsightCart\frontend\frontend"
```

First setup only:

```powershell
npm install
```

Start Vite:

```powershell
npm run dev
```

Open the URL shown by Vite, normally:

```text
http://localhost:5173
```

## 8. Normal Startup — Quick Version

### Terminal 1 — PostgreSQL

Start PostgreSQL if it is not already running.

### Terminal 2 — Backend

```powershell
cd "C:\Users\Siddhant\OneDrive\Desktop\InsightCart\InsightCart\backend\scripts"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 3 — Frontend

```powershell
cd "C:\Users\Siddhant\OneDrive\Desktop\InsightCart\InsightCart\frontend\frontend"
npm run dev
```

## 9. Frontend Validation

Before committing frontend changes:

```powershell
npm run lint
npm run build
```

## 10. Pre-Demo Checklist

- [ ] PostgreSQL is running
- [ ] `insightcart` database is accessible
- [ ] Backend starts on port `8000`
- [ ] `/api/dashboard-summary` returns data
- [ ] `/api/trends` returns data
- [ ] `/api/categories` returns data
- [ ] `/api/products` returns data
- [ ] `/api/customers` returns data
- [ ] `/api/data-quality` returns data
- [ ] `/api/reconciliation` returns data
- [ ] `/api/exceptions` returns data
- [ ] Frontend starts successfully
- [ ] Dashboard displays live API data

## 11. Security Notes

Never commit:

```text
.env
```

Database credentials must come from the environment through `DATABASE_URL`, not from source code.

## 12. Troubleshooting

### Port 8000 is already in use

```powershell
Get-NetTCPConnection -LocalPort 8000
Get-Process -Id <PID>
Stop-Process -Id <PID> -Force
```

Then start Uvicorn again.

### Frontend cannot reach the backend

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/dashboard-summary
```

If this fails, fix the backend/database connection first.

### Database connection fails

Check that:
1. PostgreSQL is running.
2. PostgreSQL is listening on port `5433`.
3. `insightcart` exists.
4. `.env` has the correct `DATABASE_URL`.
5. The PostgreSQL credentials are correct.

### Frontend dependencies are missing

```powershell
npm install
npm run dev
```

## 13. Production Build

```powershell
npm run build
```

The Vite production build is generated in `dist`.

## 14. Architecture

```text
                  ┌─────────────────────┐
                  │     React/Vite      │
                  │     Frontend        │
                  └──────────┬──────────┘
                             │ HTTP
                             ▼
                  ┌─────────────────────┐
                  │       FastAPI       │
                  │       Backend       │
                  └──────────┬──────────┘
                             │ SQLAlchemy
                             ▼
                  ┌─────────────────────┐
                  │     PostgreSQL      │
                  │      retail         │
                  │                     │
                  │ fact_sales          │
                  │ dim_customers       │
                  │ dim_products        │
                  │ dim_date            │
                  └─────────────────────┘
```

InsightCart uses PostgreSQL as the source for the analytics APIs, and the React dashboard consumes those APIs to display retail analytics.
