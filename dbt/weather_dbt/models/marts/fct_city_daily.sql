select
	city,
	date,
    mean_temperature,
	min_temperature,
	max_temperature,
    max_temperature - min_temperature as temperature_range,
	total_precipitation
from {{ ref('stg_weather') }}