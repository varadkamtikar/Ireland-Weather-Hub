import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()

def get_config(key, default=None):
    value = os.getenv(key)
    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


DB_USER = get_config("DB_USER")
DB_PASSWORD = get_config("DB_PASSWORD")
DB_HOST = get_config("DB_HOST")
DB_PORT = get_config("DB_PORT", "5432")
DB_NAME = get_config("DB_NAME")
DB_SSLMODE = get_config("DB_SSLMODE", "require")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD if DB_PASSWORD else None,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": DB_SSLMODE}
)


def get_latest_city_weather(city: str, limit: int = 3):
    query = """
        SELECT
            city,
            latitude,
            longitude,
            forecast_time,
            temperature,
            humidity,
            precipitation,
            precipitation_probability,
            pressure,
            cloud_cover,
            wind_speed,
            loaded_at
        FROM live_weather
        WHERE city = %(city)s
        ORDER BY forecast_time DESC
        LIMIT %(limit)s;
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "city": city,
            "limit": limit
        }
    )

    df = df.sort_values("forecast_time").reset_index(drop=True)

    return df


def build_prediction_features(city: str):
    df = get_latest_city_weather(city)

    if len(df) < 3:
        raise ValueError(
            f"Not enough weather rows for {city}. Need at least 3 rows."
        )

    latest_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    input_data = {
        "city": latest_row["city"],
        "latitude": latest_row["latitude"],
        "longitude": latest_row["longitude"],

        "temperature": latest_row["temperature"],
        "humidity": latest_row["humidity"],
        "precipitation": latest_row["precipitation"],
        "rain": latest_row["precipitation"],
        "pressure": latest_row["pressure"],
        "cloud_cover": latest_row["cloud_cover"],
        "wind_speed": latest_row["wind_speed"],

        "hour": pd.Timestamp(latest_row["forecast_time"]).hour,
        "day": pd.Timestamp(latest_row["forecast_time"]).day,
        "month": pd.Timestamp(latest_row["forecast_time"]).month,
        "day_of_week": pd.Timestamp(latest_row["forecast_time"]).dayofweek,

        "precipitation_lag_1": prev_row["precipitation"],
        "humidity_lag_1": prev_row["humidity"],
        "cloud_cover_lag_1": prev_row["cloud_cover"],

        "temp_rolling_3": df["temperature"].tail(3).mean(),
        "humidity_rolling_3": df["humidity"].tail(3).mean(),
    }

    return input_data


if __name__ == "__main__":
    features = build_prediction_features("Dublin")
    print(features)