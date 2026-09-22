select
    city,
    date,
    min_temperature,
    max_temperature
from {{ ref('stg_weather') }}
where max_temperature < min_temperature