select 
    city,
    date,
    temperature_2m_mean as mean_temperature,
    temperature_2m_min as min_temperature,
    temperature_2m_max as max_temperature,
    precipitation_sum as total_precipitation
from {{ source('weather', 'weather_daily') }}