import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
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

START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "pressure_msl",
    "cloud_cover",
    "wind_speed_10m",
]

API_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_city_history(city, lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": "Europe/Dublin",
    }

    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    hourly = data["hourly"]

    df = pd.DataFrame({
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "weather_time": pd.to_datetime(hourly["time"]),
        "temperature": hourly.get("temperature_2m"),
        "humidity": hourly.get("relative_humidity_2m"),
        "precipitation": hourly.get("precipitation"),
        "rain": hourly.get("rain"),
        "pressure": hourly.get("pressure_msl"),
        "cloud_cover": hourly.get("cloud_cover"),
        "wind_speed": hourly.get("wind_speed_10m"),
        "loaded_at": datetime.now(),
    })

    return df


def insert_weather_history(df):
    temp_table = "weather_history_temp"

    with engine.begin() as conn:
        df.to_sql(temp_table, conn, if_exists="replace", index=False)

        conn.execute(text("""
            INSERT INTO weather_history (
                city,
                latitude,
                longitude,
                weather_time,
                temperature,
                humidity,
                precipitation,
                rain,
                pressure,
                cloud_cover,
                wind_speed,
                loaded_at
            )
            SELECT
                city,
                latitude,
                longitude,
                weather_time,
                temperature,
                humidity,
                precipitation,
                rain,
                pressure,
                cloud_cover,
                wind_speed,
                loaded_at
            FROM weather_history_temp
            ON CONFLICT (city, weather_time)
            DO UPDATE SET
                temperature = EXCLUDED.temperature,
                humidity = EXCLUDED.humidity,
                precipitation = EXCLUDED.precipitation,
                rain = EXCLUDED.rain,
                pressure = EXCLUDED.pressure,
                cloud_cover = EXCLUDED.cloud_cover,
                wind_speed = EXCLUDED.wind_speed,
                loaded_at = EXCLUDED.loaded_at;
        """))

        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))


def main():
    all_rows = []

    for location in LOCATIONS:
        city = location["city"]
        lat = location["lat"]
        lon = location["lon"]

        print(f"Fetching historical weather for {city}...")

        df_city = fetch_city_history(city, lat, lon)
        print(f"{city}: {len(df_city)} rows")

        all_rows.append(df_city)

    final_df = pd.concat(all_rows, ignore_index=True)

    print(f"Total rows fetched: {len(final_df)}")
    insert_weather_history(final_df)
    print("Historical weather data inserted successfully.")


if __name__ == "__main__":
    main()