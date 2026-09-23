# Architecture

Optional. Most of the explanation belongs in the notebook's markdown cells; use this file
only if you have design notes that do not fit there (diagrams, alternatives you rejected).

                    config/cities.yml
                           │
                           ▼
                  ┌─────────────────┐
                  │   Open-Meteo    │
                  │   Archive API   │
                  └────────┬────────┘
                           │
                        Extract
                           │
                           ▼
                  ┌─────────────────┐
                  │ Python ingestion│
                  │   + validation  │
                  └────────┬────────┘
                           │
                          Load
                           │
                           ▼
                ┌──────────────────────┐
                │ PostgreSQL           │
                │ raw.weather_daily    │
                └──────────┬───────────┘
                           │
                         dbt
                           │
                           ▼
                ┌──────────────────────┐
                │ raw.stg_weather      │
                │ type + clean         │
                └──────────┬───────────┘
                           │
                         dbt
                           │
                           ▼
                ┌──────────────────────┐
                │ raw.fct_city_daily   │
                │ business-friendly    │
                │ daily temperature    │
                └──────────────────────┘

        Airflow:
        extract & load → dbt run → dbt test

        Notebook:
        executes the same functions
        + shows evidence + prove idempotency