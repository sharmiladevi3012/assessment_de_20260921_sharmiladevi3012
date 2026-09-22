select
    city,
    date,
    total_precipitation
from {{ ref('stg_weather') }}
where total_precipitation < 0