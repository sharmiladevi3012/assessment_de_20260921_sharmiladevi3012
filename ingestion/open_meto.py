import requests
import time


def fetch_weather(latitude, longitude, start_date, end_date) -> dict:
    """
    Fetch weather data from Open-Meteo API for the given latitude, longitude, and date range.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
	    "latitude": latitude,
	    "longitude": longitude,
	    "start_date": start_date,
	    "end_date": end_date,
	    "daily": ["temperature_2m_mean", "temperature_2m_min", "temperature_2m_max", "precipitation_sum"],
	    "timezone": "GMT",
    }

    transient_statuses = {408, 429, 500, 502, 503, 504}

    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=20)
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(0.1)
            continue

        if response.status_code == 200:
            return response.json()
        if response.status_code not in transient_statuses or attempt == 2:
            raise ValueError("Failed to fetch weather data")

        time.sleep(0.1)