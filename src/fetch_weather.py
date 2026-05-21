import requests
import pandas as pd
from datetime import datetime

LOCATIONS = [
    {"city": "Dublin", "lat": 53.3498, "lon": -6.2603},
    {"city": "Cork", "lat": 51.8985, "lon": -8.4756},
    {"city": "Galway", "lat": 53.2707, "lon": -9.0568},
    {"city": "Limerick", "lat": 52.6638, "lon": -8.6267},
    {"city": "Waterford", "lat": 52.2593, "lon": -7.1101},
    {"city": "Kilkenny", "lat": 52.6541, "lon": -7.2448},
    {"city": "Sligo", "lat": 54.2766, "lon": -8.4761},
    {"city": "Derry", "lat": 54.9966, "lon": -7.3086},
    {"city": "Athlone", "lat": 53.4239, "lon": -7.9407},
    {"city": "Killarney", "lat": 52.0599, "lon": -9.5044},
]

rows = []

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
    data = response.json()
    hourly = data["hourly"]

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
            "loaded_at": datetime.now()
        })

df = pd.DataFrame(rows)
df.to_csv("data/live_weather.csv", index=False)

print(df.head())
print("Saved file: data/live_weather.csv")