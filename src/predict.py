import os
from datetime import datetime

import joblib
import pandas as pd
from sqlalchemy import text

from src.build_prediction_features import build_prediction_features, engine


# ---------------------------------------------------
# MODEL PATHS
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "models", "xgboost_rain_model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "models", "city_label_encoder.pkl")


# ---------------------------------------------------
# LOAD MODEL AND ENCODER
# ---------------------------------------------------

model = joblib.load(MODEL_PATH)
city_encoder = joblib.load(ENCODER_PATH)


# ---------------------------------------------------
# LOW-LEVEL PREDICTION FUNCTION
# ---------------------------------------------------

def predict_rain_next_hour(input_data):
    df = pd.DataFrame([input_data])

    df["city"] = city_encoder.transform(df["city"])

    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]

    if probability >= 0.75:
        risk_level = "High"
    elif probability >= 0.50:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "rain_prediction": int(prediction),
        "rain_probability": round(float(probability) * 100, 2),
        "risk_level": risk_level
    }


# ---------------------------------------------------
# SAVE PREDICTION TO DATABASE
# ---------------------------------------------------

def save_prediction_to_db(result):
    now = datetime.now()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO rain_predictions (
                    city,
                    prediction_time,
                    rain_prediction,
                    rain_probability,
                    risk_level,
                    model_version,
                    created_at
                )
                VALUES (
                    :city,
                    :prediction_time,
                    :rain_prediction,
                    :rain_probability,
                    :risk_level,
                    :model_version,
                    :created_at
                )
            """),
            {
                "city": result["city"],
                "prediction_time": now,
                "rain_prediction": result["rain_prediction"],
                "rain_probability": result["rain_probability"],
                "risk_level": result["risk_level"],
                "model_version": "xgboost_v1",
                "created_at": now,
            }
        )


# ---------------------------------------------------
# HIGH-LEVEL CITY PREDICTION FUNCTION
# ---------------------------------------------------

def predict_city_rain(city, save_to_db=True):
    input_data = build_prediction_features(city)
    result = predict_rain_next_hour(input_data)

    final_result = {
        "city": city,
        **result
    }

    if save_to_db:
        save_prediction_to_db(final_result)

    return final_result


# ---------------------------------------------------
# TEST RUN
# ---------------------------------------------------

if __name__ == "__main__":
    cities = [
        "Dublin", "Cork", "Galway", "Limerick", "Waterford",
        "Kilkenny", "Sligo", "Athlone", "Killarney", "Derry"
    ]

    for city in cities:
        result = predict_city_rain(city)
        print(result)