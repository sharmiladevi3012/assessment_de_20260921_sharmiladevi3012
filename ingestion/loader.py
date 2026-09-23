import os

import psycopg2
import yaml
from datetime import date, timedelta
from ingestion.open_meto import fetch_weather


CREATE_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.weather_daily (
    city VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    temperature_2m_mean DECIMAL(10, 2),
    temperature_2m_min DECIMAL(10, 2),
    temperature_2m_max DECIMAL(10, 2),
    precipitation_sum DECIMAL(10, 2),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city, date)
);
"""

INSERT_SQL = """
INSERT INTO raw.weather_daily (
    city, date, latitude, longitude, timezone,
    temperature_2m_mean, temperature_2m_min,
    temperature_2m_max, precipitation_sum
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (city, date) DO UPDATE SET
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    timezone = EXCLUDED.timezone,
    temperature_2m_mean = EXCLUDED.temperature_2m_mean,
    temperature_2m_min = EXCLUDED.temperature_2m_min,
    temperature_2m_max = EXCLUDED.temperature_2m_max,
    precipitation_sum = EXCLUDED.precipitation_sum
;
"""

def _connection(db_config):
    return psycopg2.connect(
        host=db_config.get("host", "postgres"),
        port=db_config.get("port", 5432),
        dbname=db_config.get("dbname", "warehouse"),
        user=db_config.get("user", "de"),
        password=db_config.get("password", "de"),
    )


def get_db_config():
    """Read the warehouse connection details supplied by Docker Compose."""
    return {
        "host": os.environ.get("WAREHOUSE_HOST", "postgres"),
        "port": int(os.environ.get("WAREHOUSE_PORT", "5432")),
        "dbname": os.environ.get("WAREHOUSE_DB", "warehouse"),
        "user": os.environ.get("WAREHOUSE_USER", "de"),
        "password": os.environ.get("WAREHOUSE_PASSWORD", "de"),
    }


def get_cities(config_path="config/cities.yml"):
    """Read the configured cities used by the weather extraction."""
    with open(config_path, encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)["cities"]

def _rows_for_city(city, logical_date):
    latitude, longitude = city["latitude"], city["longitude"]
    weather = fetch_weather(latitude, longitude, logical_date, logical_date)
    daily = weather["daily"]
    rows = []

    for index, daily_date in enumerate(daily["time"]):
        row = (
            city["name"],
            daily_date,
            latitude,
            longitude,
            weather["timezone"],
            daily["temperature_2m_mean"][index],
            daily["temperature_2m_min"][index],
            daily["temperature_2m_max"][index],
            daily["precipitation_sum"][index],
        )
        rows.append(row)

    return rows


def extract_weather_for_date(cities, logical_date):
    """Extract raw weather rows for one logical date without writing to Postgres."""
    rows = []
    for city in cities:
        rows.extend(_rows_for_city(city, logical_date))
    return rows


def load_weather_rows(rows, logical_date, db_config):
    """Idempotently load extracted rows for one logical date using upsert."""
    with _connection(db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
            if rows:
                cursor.executemany(INSERT_SQL, rows)


def load_weather_for_date(cities, logical_date, db_config):
    """Fetch and idempotently load weather for one logical date."""
    rows = extract_weather_for_date(cities, logical_date)
    load_weather_rows(rows, logical_date, db_config)


def load_weather_for_date_range(cities, start_date, end_date, db_config):
    """Load each date separately so the helper is suitable for backfills."""
    current_date = date.fromisoformat(start_date)
    last_date = date.fromisoformat(end_date)

    while current_date <= last_date:
        load_weather_for_date(cities, current_date.isoformat(), db_config)
        current_date += timedelta(days=1)
