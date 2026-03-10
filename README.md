# Running History

A local app to aggregate and visualize 20+ years of running data from Garmin, Strava, Nike Run Club, Runkeeper, Polar, and Suunto into a single unified view.

## Features

- Import from Garmin, Strava, Nike, Runkeeper, Polar/Suunto bulk exports
- Automatic deduplication — runs that appear in multiple sources are merged cleanly
- Strava OAuth sync — incremental, pulls new runs automatically
- Dashboard with yearly distance and pace trend charts
- Activity list with filters (year, source, type, distance)
- Per-activity detail with full stats and GPS route map
- Analytics: HR zones, personal records, streak, pace trends, monthly breakdown
- Full heatmap of all GPS tracks

---

## Quick Start

Double-click `start.command` in Finder to start both the backend and frontend and open the app in your browser.

---

## Manual Setup

### Prerequisites

- Python 3.9+
- Node.js 18+

### Backend

```bash
cd running_history
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
cp .env.example .env            # fill in your credentials (see below)
python migrations/init_db.py    # create the SQLite database
uvicorn main:app --reload       # API runs at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # runs at http://localhost:5173
```

---

## Importing Your Data

### Step 1: Request your exports

Some services take time to prepare your data — request these first.

| Source | How to export | Wait time |
|---|---|---|
| **Garmin** | garmin.com → Account → Data Management → Export Your Data | Minutes |
| **Strava** | strava.com → Settings → My Account → Download or Delete → Request archive | Minutes–hours |
| **Nike Run Club** | nike.com → Privacy Settings → Request your data (GDPR) | 24–48 hours |
| **Runkeeper** | App → Settings → Export Data | Instant |
| **Polar** | flow.polar.com → Account → Export training data | Minutes |
| **Suunto** | suunto.com → Account → Export data | Minutes |

### Step 2: Place files in the data directory

```
data/raw/
├── garmin/          # unzipped Garmin export (contains Activities/ folder with .fit files)
├── strava/          # unzipped Strava export (contains activities.csv + activity files)
├── nike/            # Nike GDPR export (contains NRC/ folder with JSON files)
├── runkeeper/       # Runkeeper export (contains cardioActivities.csv + GPX files)
└── polar_suunto/    # .fit, .gpx, or .tcx files
```

### Step 3: Run the importer

```bash
cd backend
source ../.venv/bin/activate
python scripts/import_all.py
```

The importer will process all sources, normalize everything to the same units (meters, seconds, decimal degrees, UTC), and skip any duplicates it detects across sources.

---

## Strava Live Sync

To pull new runs from Strava automatically (without re-importing a bulk export):

1. Create an API application at strava.com/settings/api
2. Set **Authorization Callback Domain** to `localhost`
3. Add your credentials to `backend/.env`:
   ```
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```
4. In the app sidebar, click **Connect Strava** → authorize → click **Sync Now**

---

## API

The backend exposes a REST API at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/activities` | List/filter activities (page, year, source, type, distance) |
| GET | `/api/activities/{id}` | Single activity detail |
| GET | `/api/activities/{id}/route` | Simplified GPS polyline |
| DELETE | `/api/activities/{id}` | Delete an activity |
| GET | `/api/analytics/summary` | Totals: runs, distance, time, elevation, years active |
| GET | `/api/analytics/by-year` | Per-year breakdown |
| GET | `/api/analytics/by-month` | Per-month breakdown (optionally filtered by year) |
| GET | `/api/analytics/pace-trend` | Pace trend over time |
| GET | `/api/analytics/hr-zones` | HR zone distribution |
| GET | `/api/analytics/personal-records` | PRs for 1k, 1mi, 5k, 10k, half, marathon |
| GET | `/api/analytics/longest-streak` | Longest running streak |
| GET | `/api/analytics/sources` | Per-source counts and date ranges |
| GET | `/api/routes/all-tracks` | Simplified polylines for the heatmap |
| GET | `/auth/strava` | Start Strava OAuth flow |
| POST | `/api/sync/strava` | Incremental sync of new Strava activities |

---

## Project Structure

```
running_history/
├── start.command              # Double-click to launch everything
├── backend/
│   ├── main.py                # FastAPI app, CORS, router registration
│   ├── config.py              # Settings via pydantic-settings + .env
│   ├── database.py            # SQLAlchemy engine + session
│   ├── models.py              # ORM models
│   ├── schemas.py             # Pydantic response schemas
│   ├── routers/
│   │   ├── activities.py      # List/filter/detail/delete
│   │   ├── analytics.py       # Aggregations, PRs, streaks, HR zones
│   │   ├── routes.py          # GPS route + heatmap data
│   │   ├── auth.py            # Strava OAuth2 flow
│   │   └── sync.py            # Strava incremental sync
│   ├── ingestion/
│   │   ├── base.py            # NormalizedActivity dataclass + BaseImporter ABC
│   │   ├── deduplication.py   # Overlap detection (±2min / ±2% distance)
│   │   ├── garmin.py          # FIT bulk export
│   │   ├── strava.py          # CSV + GPX/FIT bulk export
│   │   ├── nike.py            # Nike GDPR JSON
│   │   ├── runkeeper.py       # CSV + GPX
│   │   └── polar_suunto.py    # FIT / GPX / TCX
│   ├── utils/
│   │   ├── fit_parser.py      # fitparse wrapper
│   │   ├── gpx_parser.py      # gpxpy + TCX parser
│   │   ├── geo.py             # Douglas-Peucker route simplification
│   │   └── hr_zones.py        # HR zone calculation
│   ├── scripts/
│   │   └── import_all.py      # CLI: run all importers
│   ├── migrations/
│   │   └── init_db.py         # Create database tables (idempotent)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/               # Axios client + per-resource API modules
│       ├── components/        # Dashboard, activity list, maps
│       ├── pages/             # Dashboard, Activities, Analytics, Heatmap
│       ├── hooks/             # React Query hooks
│       └── types/index.ts     # TypeScript interfaces
└── data/
    ├── raw/                   # Drop exports here (gitignored)
    └── running_history.db     # SQLite database (gitignored)
```

---

## Stack

**Backend**: FastAPI, SQLAlchemy 2, SQLite, fitparse, gpxpy, requests, pydantic-settings

**Frontend**: React + Vite + TypeScript, Recharts, Leaflet, React Query, Tailwind CSS, Axios
