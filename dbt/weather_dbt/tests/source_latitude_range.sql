select
    city,
    date,
    latitude
from {{ source('weather', 'weather_daily') }}
where latitude < -90 or latitude > 90