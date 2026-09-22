select
    city,
    date,
    longitude
from {{ source('weather', 'weather_daily') }}
where longitude < -180 or longitude > 180