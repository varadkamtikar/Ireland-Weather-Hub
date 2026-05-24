import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD if DB_PASSWORD else None,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL)

# ---------------------------------------------------
# CREATE PREPARED ML TABLE
# ---------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prepared_ml_dataset (
    id SERIAL PRIMARY KEY,

    city VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    weather_time TIMESTAMP,

    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    rain DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    cloud_cover DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,

    loaded_at TIMESTAMP,

    hour INTEGER,
    day INTEGER,
    month INTEGER,
    day_of_week INTEGER,

    precipitation_lag_1 DOUBLE PRECISION,
    humidity_lag_1 DOUBLE PRECISION,
    cloud_cover_lag_1 DOUBLE PRECISION,

    temp_rolling_3 DOUBLE PRECISION,
    humidity_rolling_3 DOUBLE PRECISION,

    rain_next_hour INTEGER,

    prepared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_prepared_city_time UNIQUE (city, weather_time)
);
"""

# ---------------------------------------------------
# LOAD RAW HISTORICAL DATA
# ---------------------------------------------------

def load_weather_history():
    query = """
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
    FROM weather_history
    ORDER BY city, weather_time;
    """

    df = pd.read_sql(query, engine)
    return df


# ---------------------------------------------------
# FEATURE ENGINEERING
# ---------------------------------------------------

def prepare_features(df):
    print("Original Shape:", df.shape)

    df["weather_time"] = pd.to_datetime(df["weather_time"])

    # -------------------------------
    # TIME FEATURES
    # -------------------------------

    df["hour"] = df["weather_time"].dt.hour
    df["day"] = df["weather_time"].dt.day
    df["month"] = df["weather_time"].dt.month
    df["day_of_week"] = df["weather_time"].dt.dayofweek

    # -------------------------------
    # LAG FEATURES
    # -------------------------------

    df["precipitation_lag_1"] = (
        df.groupby("city")["precipitation"].shift(1)
    )

    df["humidity_lag_1"] = (
        df.groupby("city")["humidity"].shift(1)
    )

    df["cloud_cover_lag_1"] = (
        df.groupby("city")["cloud_cover"].shift(1)
    )

    # -------------------------------
    # ROLLING FEATURES
    # -------------------------------

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

    # -------------------------------
    # TARGET VARIABLE
    # -------------------------------

    df["rain_next_hour"] = (
        df.groupby("city")["precipitation"]
        .shift(-1)
        .gt(0)
        .astype(int)
    )

    # -------------------------------
    # REMOVE NULL VALUES
    # -------------------------------

    df = df.dropna().copy()

    df["rain_next_hour"] = df["rain_next_hour"].astype(int)

    df["prepared_at"] = pd.Timestamp.now()

    print("Final Shape:", df.shape)

    return df


# ---------------------------------------------------
# SAVE TO CSV
# ---------------------------------------------------

def save_to_csv(df):
    os.makedirs("data", exist_ok=True)

    output_path = "data/ml_weather_dataset.csv"

    df.to_csv(output_path, index=False)

    print(f"Dataset saved to CSV: {output_path}")


# ---------------------------------------------------
# SAVE TO POSTGRESQL
# ---------------------------------------------------

def save_to_postgres(df):
    temp_table = "prepared_ml_dataset_temp"

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))

        df.to_sql(
            temp_table,
            conn,
            if_exists="replace",
            index=False
        )

        conn.execute(text("""
            INSERT INTO prepared_ml_dataset (
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
                loaded_at,
                hour,
                day,
                month,
                day_of_week,
                precipitation_lag_1,
                humidity_lag_1,
                cloud_cover_lag_1,
                temp_rolling_3,
                humidity_rolling_3,
                rain_next_hour,
                prepared_at
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
                loaded_at,
                hour,
                day,
                month,
                day_of_week,
                precipitation_lag_1,
                humidity_lag_1,
                cloud_cover_lag_1,
                temp_rolling_3,
                humidity_rolling_3,
                rain_next_hour,
                prepared_at
            FROM prepared_ml_dataset_temp
            ON CONFLICT (city, weather_time)
            DO UPDATE SET
                temperature = EXCLUDED.temperature,
                humidity = EXCLUDED.humidity,
                precipitation = EXCLUDED.precipitation,
                rain = EXCLUDED.rain,
                pressure = EXCLUDED.pressure,
                cloud_cover = EXCLUDED.cloud_cover,
                wind_speed = EXCLUDED.wind_speed,
                loaded_at = EXCLUDED.loaded_at,
                hour = EXCLUDED.hour,
                day = EXCLUDED.day,
                month = EXCLUDED.month,
                day_of_week = EXCLUDED.day_of_week,
                precipitation_lag_1 = EXCLUDED.precipitation_lag_1,
                humidity_lag_1 = EXCLUDED.humidity_lag_1,
                cloud_cover_lag_1 = EXCLUDED.cloud_cover_lag_1,
                temp_rolling_3 = EXCLUDED.temp_rolling_3,
                humidity_rolling_3 = EXCLUDED.humidity_rolling_3,
                rain_next_hour = EXCLUDED.rain_next_hour,
                prepared_at = EXCLUDED.prepared_at;
        """))

        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))

    print("Prepared ML dataset saved to PostgreSQL table: prepared_ml_dataset")


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

def main():
    print("Loading historical weather data from PostgreSQL...")

    df = load_weather_history()

    if df.empty:
        raise ValueError("weather_history table is empty. Run historical data collection first.")

    print("Preparing ML features...")

    prepared_df = prepare_features(df)

    print("Saving prepared dataset to CSV...")

    save_to_csv(prepared_df)

    print("Saving prepared dataset to PostgreSQL...")

    save_to_postgres(prepared_df)

    print("Done. ML dataset is ready.")


if __name__ == "__main__":
    main()