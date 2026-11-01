"ЕТАП 1: створити таблицю weather (все в одній купі)"
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

WIND_DIRECTIONS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

def upgrade() -> None:
    # Міграція описує таблицю явно, а не бере її з поточних моделей:
    # моделі з часом змінюються, а міграція — це "знімок історії" і має завжди працювати однаково.
    op.create_table(
        "weather",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("wind_degree", sa.Integer(), nullable=False),
        sa.Column("wind_kph", sa.Double(), nullable=False),
        sa.Column("wind_direction", sa.Enum(*WIND_DIRECTIONS, name="wind_direction_enum"), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.Column("sunrise", sa.Time(), nullable=True),
        sa.Column("location_name", sa.String(150), nullable=False),
        sa.Column("condition_text", sa.String(100), nullable=False),
        sa.Column("temperature_celsius", sa.Double(), nullable=False),
        sa.Column("precip_mm", sa.Double(), nullable=False),
        sa.Column("precip_in", sa.Double(), nullable=False),
        sa.Column("humidity", sa.Integer(), nullable=False),
        sa.Column("cloud", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_weather"),
    )
    op.create_index("ix_weather_country_last_updated", "weather", ["country", "last_updated"])

def downgrade() -> None:
    op.drop_index("ix_weather_country_last_updated", table_name="weather")
    op.drop_table("weather")
    # У PostgreSQL тип enum живе окремо від таблиці - його треба видалити вручну.
    sa.Enum(name="wind_direction_enum").drop(op.get_bind(), checkfirst=True)
