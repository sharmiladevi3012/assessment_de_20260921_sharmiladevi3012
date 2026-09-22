select
    city,
    date,
    count(*) as row_count
from {{ ref('fct_city_daily') }}
group by city, date
having count(*) > 1