# 🇮🇪 Ireland Weather Hub

A real-time weather monitoring and analytics dashboard for 10 Irish cities, built with Python and Streamlit. Pulls live 24-hour forecasts from the Open-Meteo API, stores them in PostgreSQL (with a CSV fallback), and visualises rainfall, temperature, wind, and pressure on an interactive map and chart suite.

---

## Live Demo

> Run locally — see [Quick Start](#quick-start) below.

---

## Features

### Dashboard

| Section | What it shows |
|---|---|
| **Hero Banner** | Date/time, active city count, data source, last sync time |
| **KPI Cards** | Peak rain probability · Wettest location · Average temperature · Active rain zones (≥ 70 % chance) |
| **City Snapshots** | Per-city cards with weather icon, temperature, precipitation, wind label, and rain intensity badge |
| **Live Rainfall Map** | Mapbox scatter map colour-coded by rain probability; click any dot to zoom in, click again to reset |
| **24-Hour Analytics** | Four tabs — Rainfall, Temperature & Humidity, Wind & Pressure, Hour Snapshot radar |
| **Raw Data** | Expandable table for the selected forecast hour with progress-bar columns |

### Sidebar Controls

- **Refresh** — re-fetches data on demand (PostgreSQL first, CSV fallback)
- **City filter** — multiselect (default: all 10 cities; "All Cities" chip selects everything)
- **Forecast hour** — slider across the 24-hour window
- **Rain threshold** — show only cities above a minimum probability %
- **Data source badge** — green = PostgreSQL live, yellow = CSV cache

---

## Cities Covered

| City | Lat | Lon |
|---|---|---|
| Dublin | 53.3498 | −6.2603 |
| Cork | 51.8985 | −8.4756 |
| Galway | 53.2707 | −9.0568 |
| Limerick | 52.6638 | −8.6267 |
| Waterford | 52.2593 | −7.1101 |
| Kilkenny | 52.6541 | −7.2448 |
| Sligo | 54.2766 | −8.4761 |
| Derry | 54.9966 | −7.3086 |
| Athlone | 53.4239 | −7.9407 |
| Killarney | 52.0599 | −9.5044 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit, Plotly Express, Plotly Graph Objects |
| Data Wrangling | Pandas, NumPy |
| Database | PostgreSQL via SQLAlchemy + psycopg2 |
| Weather API | Open-Meteo (free, no API key required) |
| Machine Learning | XGBoost, Scikit-learn |
| Configuration | python-dotenv |
| Visual Analytics | Tableau |

---

## Project Structure

```text
Ireland-Weather-Hub/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── .env
│
├── data/
│   ├── live_weather.csv
│   └── ml_weather_dataset.csv
│
├── notebooks/
│   └── XGBoost_Rainfall_Prediction.ipynb
│
├── src/
│   ├── fetch_weather.py
│   ├── fetch_weather_to_postgres.py
│   ├── fetch_historical_weather.py
│   └── prepare_ml_dataset.py
│
└── Ireland Rainfall Dashboard.twb
```

---

## Data Pipeline

```text
Open-Meteo Forecast API
        │
        ├─── fetch_weather.py ──────────────► data/live_weather.csv
        │                                           │
        └─── fetch_weather_to_postgres.py ─► PostgreSQL: live_weather
                                                    │
                                                    ▼
                                              app.py (reads both,
                                              PostgreSQL preferred)

Open-Meteo Archive API
        │
        └─── fetch_historical_weather.py ──► PostgreSQL: weather_history
                                                    │
                                                    ▼
                                          prepare_ml_dataset.py
                                                    │
                                                    ▼
                                          data/ml_weather_dataset.csv
```

---

## Variables Fetched Per City Per Hour

| Column | Description |
|---|---|
| `temperature` | Temperature at 2m (°C) |
| `humidity` | Relative humidity (%) |
| `precipitation` | Rainfall amount (mm) |
| `precipitation_probability` | Rain probability (%) |
| `pressure` | Mean sea-level pressure (hPa) |
| `cloud_cover` | Total cloud cover (%) |
| `wind_speed` | Wind speed at 10m (km/h) |

---

## PostgreSQL Schema

### `live_weather`

```sql
city                      TEXT
latitude                  FLOAT
longitude                 FLOAT
forecast_time             TIMESTAMP
temperature               FLOAT
humidity                  FLOAT
precipitation             FLOAT
precipitation_probability FLOAT
pressure                  FLOAT
cloud_cover               FLOAT
wind_speed                FLOAT
loaded_at                 TIMESTAMP
```

### `weather_history`

```sql
city          TEXT
latitude      FLOAT
longitude     FLOAT
weather_time  TIMESTAMP
temperature   FLOAT
humidity      FLOAT
precipitation FLOAT
rain          FLOAT
pressure      FLOAT
cloud_cover   FLOAT
wind_speed    FLOAT
loaded_at     TIMESTAMP

UNIQUE (city, weather_time)
```

---

## ML Dataset

`prepare_ml_dataset.py` engineers features for rainfall prediction.

### Engineered Features

| Feature | Description |
|---|---|
| `hour`, `day`, `month`, `day_of_week` | Time-based features |
| `precipitation_lag_1` | Rainfall lag feature |
| `humidity_lag_1` | Humidity lag feature |
| `cloud_cover_lag_1` | Cloud lag feature |
| `temp_rolling_3` | Rolling temperature mean |
| `humidity_rolling_3` | Rolling humidity mean |
| `rain_next_hour` | Binary rainfall prediction target |

Output:

```text
data/ml_weather_dataset.csv
```

---

# Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/varadkamtikar/Ireland-Weather-Hub.git
cd Ireland-Weather-Hub
```

---

## 2. Create Virtual Environment

### Mac/Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then update `.env` with your PostgreSQL / Neon database credentials.

Example:

```env
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=your_neon_host
DB_PORT=5432
DB_NAME=your_database_name
DB_SSLMODE=require
```

> If PostgreSQL is unavailable, the dashboard automatically falls back to CSV mode.

---

## 5. Fetch Live Weather Data

### CSV Mode

```bash
python src/fetch_weather.py
```

### PostgreSQL Mode

```bash
python src/fetch_weather_to_postgres.py
```

---

## 6. Run Streamlit Dashboard

```bash
streamlit run app.py
```

Open in browser:

```text
http://localhost:8501
```

---

# Optional: Historical Weather Pipeline

## Fetch Historical Weather Data

```bash
python src/fetch_historical_weather.py
```

Pulls hourly weather data for all cities between:

```text
2024-01-01 → 2025-12-31
```

---

## Build ML Dataset

```bash
python src/prepare_ml_dataset.py
```

Creates:

```text
data/ml_weather_dataset.csv
```

---

## Data Refresh Logic

The dashboard uses:

```python
@st.cache_data(ttl=300)
```

to cache weather data for 5 minutes.

Refresh workflow:

1. Attempts PostgreSQL ingestion
2. Falls back to CSV ingestion
3. Displays an error if both fail

Sidebar badge indicators:

- 🟢 PostgreSQL Live
- 🟡 CSV Fallback

---

## Data Source

Weather data provided by:

### Open-Meteo

https://open-meteo.com

Endpoints used:

- `/v1/forecast`
- `/v1/archive`

Features:

- Free API
- No API key required
- Open-source weather service

---

## Future Improvements

- Public cloud deployment
- Docker containerisation
- Scheduled ETL workflows
- CI/CD with GitHub Actions
- Advanced rainfall forecasting
- Severe weather alerts
- Time-series forecasting models

---

# Author

## Varad Kamtikar

MSc Data Science — TU Dublin

GitHub:  
https://github.com/varadkamtikar

LinkedIn:  
https://www.linkedin.com/in/varadkamtikar