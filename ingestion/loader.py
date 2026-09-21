import psycopg2
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
    PRIMARY KEY (city, date)
);
"""

DELETE_SQL = "DELETE FROM raw.weather_daily WHERE date = %s;"

INSERT_SQL = """
INSERT INTO raw.weather_daily (
    city, date, latitude, longitude, timezone,
    temperature_2m_mean, temperature_2m_min,
    temperature_2m_max, precipitation_sum
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
;
"""

def _connection(db_config):
    return psycopg2.connect(
        host=db_config["localhost"],
        port=db_config.get("port", 5432),
        dbname=db_config["warehouse"],
        user=db_config["db"],
        password=db_config["db"],
    )

def _rows_for_city(city, logical_date):
    latitude, longitude = city["latitude"], city["longitude"]
    weather = fetch_weather(latitude, longitude, logical_date, logical_date)
    daily = weather["daily"]
    daily_units = weather["daily_units"]
    rows = []

    for index, daily_date in enumerate(daily["time"]):
        row = (
            city["name"],
            daily_date,
            latitude,
            longitude,
            weather["timezone"],
            daily_units["temperature_2m_mean"][index],
            daily_units["temperature_2m_min"][index],
            daily_units["temperature_2m_max"][index],
            daily_units["precipitation_sum"][index],
        )
        rows.append(row)

    return rows


def load_weather_for_date(cities, logical_date, db_config):
    """Fetch and idempotently load weather for one logical date."""
    rows = []
    for city in cities:
        city_rows = _rows_for_city(city, logical_date)
        rows.extend(city_rows)

    with _connection(db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
            cursor.execute(DELETE_SQL, (logical_date,))
            if rows:
                cursor.executemany(INSERT_SQL, rows)


def load_weather_for_date_range(cities, start_date, end_date, db_config):
    """Load each date separately so the helper is suitable for backfills."""
    current_date = date.fromisoformat(start_date)
    last_date = date.fromisoformat(end_date)

    while current_date <= last_date:
        load_weather_for_date(cities, current_date.isoformat(), db_config)
        current_date += timedelta(days=1)
