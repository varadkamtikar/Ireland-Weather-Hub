import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD if DB_PASSWORD else None,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL)

LOCATIONS = [
    {"city": "Dublin", "lat": 53.3498, "lon": -6.2603},
    {"city": "Cork", "lat": 51.8985, "lon": -8.4756},
    {"city": "Galway", "lat": 53.2707, "lon": -9.0568},
    {"city": "Limerick", "lat": 52.6638, "lon": -8.6267},
    {"city": "Waterford", "lat": 52.2593, "lon": -7.1101},
    {"city": "Kilkenny", "lat": 52.6541, "lon": -7.2448},
    {"city": "Sligo", "lat": 54.2766, "lon": -8.4761},
    {"city": "Athlone", "lat": 53.4239, "lon": -7.9407},
    {"city": "Killarney", "lat": 52.0599, "lon": -9.5044},
    {"city": "Derry", "lat": 54.9966, "lon": -7.3086},
]

rows = []
batch_loaded_at = datetime.now()

for loc in LOCATIONS:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        "&hourly=temperature_2m,relative_humidity_2m,precipitation,"
        "precipitation_probability,pressure_msl,cloud_cover,wind_speed_10m"
        "&forecast_days=1"
        "&timezone=Europe%2FDublin"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()
    hourly = data["hourly"]

    print(f"Fetched {loc['city']}: {len(hourly['time'])} hourly rows")

    for i in range(len(hourly["time"])):
        rows.append({
            "city": loc["city"],
            "latitude": loc["lat"],
            "longitude": loc["lon"],
            "forecast_time": hourly["time"][i],
            "temperature": hourly["temperature_2m"][i],
            "humidity": hourly["relative_humidity_2m"][i],
            "precipitation": hourly["precipitation"][i],
            "precipitation_probability": hourly["precipitation_probability"][i],
            "pressure": hourly["pressure_msl"][i],
            "cloud_cover": hourly["cloud_cover"][i],
            "wind_speed": hourly["wind_speed_10m"][i],
            "loaded_at": batch_loaded_at,
        })

df = pd.DataFrame(rows)

print("Total rows prepared:", len(df))
print(df["city"].value_counts())

df["forecast_time"] = pd.to_datetime(df["forecast_time"])
df["loaded_at"] = pd.to_datetime(df["loaded_at"])

df.to_sql(
    "live_weather",
    engine,
    if_exists="append",
    index=False,
)

print(f"Inserted {len(df)} rows into PostgreSQL.")