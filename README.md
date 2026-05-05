# Waste Management System (FastAPI + MySQL)

Waste Management System is a FastAPI web application that predicts a routing action for waste collection and, when needed, finds the nearest disposal location.

The system is now fully database-backed (MySQL) for both:
- operational data (locations, waste records, disposal points, legacy rules)
- mined Apriori rules used for prediction

---

## Features

- User registration and login
- Dashboard-based route decision
- Three decision outputs:
  - `WAIT`
  - `MONITOR`
  - `DISPOSE`
- Nearest disposal location lookup when decision is `DISPOSE`
- Apriori rule mining from database tables
- Rule storage and inference from MySQL (`apriori_rules`)

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- MySQL + PyMySQL
- Pandas
- mlxtend (Apriori + association rules)
- Jinja2 templates

---

## Project Structure

```text
Waste_Management_System/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── routes/
│   │   ├── user.py
│   │   └── prediction.py
│   └── services/
│       ├── apriori_engine.py
│       └── distance.py
├── scripts/
│   └── mine_apriori.py
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── map.html
├── dataset/
│   └── apriori_meta.json
└── requirements.txt
```

---

## How the System Works

### 1) Prediction flow

1. User submits form on `dashboard` (`waste`, `delay`, `density`, `area`, `lat`, `lon`).
2. `app/routes/prediction.py` calls `apriori_decision(...)`.
3. `app/services/apriori_engine.py` reads candidate rules from MySQL table `apriori_rules`.
4. Best rule is selected by:
   - larger antecedent size
   - higher lift
   - higher confidence
5. Decision is returned as `WAIT` / `MONITOR` / `DISPOSE`.
6. If `DISPOSE`, `app/services/distance.py` finds nearest row from MySQL table `disposal_locations` and returns map coordinates.

### 2) Rule mining flow

1. Run `scripts/mine_apriori.py`.
2. Script reads `waste_data` and `location_data` tables.
3. It generates transactions and mines association rules.
4. Action rules are stored into `apriori_rules`.
5. Metadata is written to `dataset/apriori_meta.json`.

---

## Database Schema

The app auto-creates tables via SQLAlchemy models on startup:

- `users`
- `location_data`
- `waste_data`
- `disposal_locations`
- `legacy_rules`
- `apriori_rules`

### Key table usage

- `apriori_rules`: primary decision source
- `legacy_rules`: fallback decision source if `apriori_rules` is empty
- `disposal_locations`: nearest-bin calculation source
- `waste_data` + `location_data`: Apriori mining input

---

## Prerequisites

- Python 3.10+ recommended
- MySQL Server running locally
- A MySQL database named `waste_db`

---

## Setup Instructions

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd Waste_Management_System
```

### 2) Create virtual environment and install dependencies

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure database connection

Connection is currently defined in `app/database.py`:

```python
DATABASE_URL = "mysql+pymysql://root:<password>@localhost/waste_db"
```

Update it to your own MySQL username/password/host/database before running.

### 4) Start API server

```bash
uvicorn app.main:app --reload
```

App will be available at: `http://127.0.0.1:8000`

---

## First-Time Data Preparation

Since operational dataset CSV files are retired, use one of these:

- restore from an existing MySQL dump of `waste_db`, or
- insert seed data into:
  - `location_data`
  - `waste_data`
  - `disposal_locations`
  - `legacy_rules`

After data is present, run rule mining:

```bash
python scripts/mine_apriori.py
```

This populates `apriori_rules`.

---

## Main Routes

- `GET /` -> Login page
- `POST /` -> Login action
- `GET /register` -> Register page
- `POST /register` -> Register action
- `GET /dashboard` -> Waste routing dashboard
- `POST /predict` -> Decision prediction + nearest disposal location (for `DISPOSE`)
- `GET /map` -> Map page template

---

## Quick Functional Test

Use these dashboard input combinations:

### Expect `WAIT`
- Waste: Low (`0`)
- Delay: `0`
- Density: Low (`0`)
- Area: Residential (`0`)

### Expect `MONITOR`
- Waste: Medium (`1`)
- Delay: `1`
- Density: High (`2`)
- Area: Residential (`0`)

### Expect `DISPOSE`
- Waste: High (`2`)
- Delay: `1`
- Density: High (`2`)
- Area: Residential (`0`)

Latitude/Longitude can be any valid values (for example `12.9716`, `77.5946`).

---

## Useful SQL Checks

### Confirm data exists

```sql
SELECT COUNT(*) FROM location_data;
SELECT COUNT(*) FROM waste_data;
SELECT COUNT(*) FROM disposal_locations;
SELECT COUNT(*) FROM legacy_rules;
SELECT COUNT(*) FROM apriori_rules;
```

### Inspect top mined rules

```sql
SELECT antecedents, consequents, support, confidence, lift
FROM apriori_rules
ORDER BY lift DESC, confidence DESC
LIMIT 10;
```

### Verify nearest disposal row for a point

```sql
SELECT disposal_id, latitude, longitude,
       ((latitude-12.9716)*(latitude-12.9716) + (longitude-77.5946)*(longitude-77.5946)) AS d2
FROM disposal_locations
ORDER BY d2 ASC
LIMIT 1;
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`
- Run commands from project root (`Waste_Management_System`).

### MySQL authentication/connection error
- Recheck `DATABASE_URL` in `app/database.py`.
- Confirm MySQL service is running.
- Confirm database `waste_db` exists.

### Dashboard always returns `WAIT`
- Check if `apriori_rules` has rows.
- If empty, rerun:
  - `python scripts/mine_apriori.py`

### No map shown for `DISPOSE`
- Ensure `disposal_locations` table has rows with valid latitude/longitude.

---

## Notes

- `dataset/apriori_meta.json` stores metadata only (not rules).
- Prediction priority is mined rules first (`apriori_rules`), then `legacy_rules` fallback.
- Distance currently uses Euclidean lat/lon difference for nearest selection.

---

## Future Improvements (Suggested)

- Move `DATABASE_URL` to environment variables (`.env`) for safer credentials handling.
- Add automated tests for:
  - decision output coverage (`WAIT`, `MONITOR`, `DISPOSE`)
  - nearest-disposal correctness
- Add Alembic migrations for schema versioning.
- Add seed script + SQL dump versioning for reproducible setup.

