import os

DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/weather_pg"

def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
