import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

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

query = """
SELECT *
FROM weather_history
ORDER BY city, weather_time
"""

df = pd.read_sql(query, engine)

print("Original Shape:", df.shape)

# ---------------------------------------------------
# TIME FEATURES
# ---------------------------------------------------

df["weather_time"] = pd.to_datetime(df["weather_time"])

df["hour"] = df["weather_time"].dt.hour
df["day"] = df["weather_time"].dt.day
df["month"] = df["weather_time"].dt.month
df["day_of_week"] = df["weather_time"].dt.dayofweek

# ---------------------------------------------------
# LAG FEATURES
# ---------------------------------------------------

df["precipitation_lag_1"] = (
    df.groupby("city")["precipitation"].shift(1)
)

df["humidity_lag_1"] = (
    df.groupby("city")["humidity"].shift(1)
)

df["cloud_cover_lag_1"] = (
    df.groupby("city")["cloud_cover"].shift(1)
)

# ---------------------------------------------------
# ROLLING FEATURES
# ---------------------------------------------------

df["temp_rolling_3"] = (
    df.groupby("city")["temperature"]
    .rolling(window=3)
    .mean()
    .reset_index(level=0, drop=True)
)

df["humidity_rolling_3"] = (
    df.groupby("city")["humidity"]
    .rolling(window=3)
    .mean()
    .reset_index(level=0, drop=True)
)

# ---------------------------------------------------
# TARGET VARIABLE
# ---------------------------------------------------

df["rain_next_hour"] = (
    df.groupby("city")["precipitation"]
    .shift(-1)
    .gt(0)
    .astype(int)
)

# ---------------------------------------------------
# REMOVE NULLS
# ---------------------------------------------------

df = df.dropna()

print("Final Shape:", df.shape)

# ---------------------------------------------------
# SAVE DATASET
# ---------------------------------------------------

output_path = "data/ml_weather_dataset.csv"

os.makedirs("data", exist_ok=True)

df.to_csv(output_path, index=False)

print(f"Dataset saved to: {output_path}")