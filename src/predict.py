import os
import joblib
import pandas as pd


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
# PREDICTION FUNCTION
# ---------------------------------------------------

def predict_rain_next_hour(input_data):
    """
    Predict whether it will rain in the next hour.

    input_data must be a dictionary with the same feature names
    used during model training.
    """

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
# TEST RUN
# ---------------------------------------------------

if __name__ == "__main__":

    sample_input = {
        "city": "Dublin",
        "latitude": 53.3498,
        "longitude": -6.2603,
        "temperature": 12.5,
        "humidity": 85,
        "precipitation": 0.2,
        "rain": 0.2,
        "pressure": 1012,
        "cloud_cover": 90,
        "wind_speed": 18,
        "hour": 14,
        "day": 21,
        "month": 5,
        "day_of_week": 3,
        "precipitation_lag_1": 0.0,
        "humidity_lag_1": 82,
        "cloud_cover_lag_1": 88,
        "temp_rolling_3": 12.1,
        "humidity_rolling_3": 83.5,
    }

    result = predict_rain_next_hour(sample_input)

    print(result)