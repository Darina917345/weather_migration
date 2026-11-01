"ЕТАП 2: винести дані про опади в окрему таблицю precipitation (рефакторинг)"
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) нова таблиця. Зв'язок 1:1 — унікальний зовнішній ключ weather_id
    op.create_table(
        "precipitation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("weather_id", sa.Integer(), nullable=False),
        sa.Column("precip_mm", sa.Double(), nullable=False),
        sa.Column("precip_in", sa.Double(), nullable=False),
        sa.Column("humidity", sa.Integer(), nullable=False),
        sa.Column("cloud", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_precipitation"),
        sa.ForeignKeyConstraint(["weather_id"], ["weather.id"],
                                name="fk_precipitation_weather_id_weather",
                                ondelete="CASCADE"),
        sa.UniqueConstraint("weather_id", name="uq_precipitation_weather_id"),
    )

    # 2) копіюємо дані. Один SQL-запит у самій БД — швидко і однаково працює і в PostgreSQL, і в MySQL.
    op.execute(
        "INSERT INTO precipitation (weather_id, precip_mm, precip_in, humidity, cloud) "
        "SELECT id, precip_mm, precip_in, humidity, cloud FROM weather"
    )

    # 3) прибираємо старі колонки
    for col in ("precip_mm", "precip_in", "humidity", "cloud"):
        op.drop_column("weather", col)

def downgrade() -> None:
    # Зворотній шлях: повернути колонки (поки порожні), перенести дані назад, потім зробити NOT NULL і видалити нову таблицю.
    op.add_column("weather", sa.Column("precip_mm", sa.Double(), nullable=True))
    op.add_column("weather", sa.Column("precip_in", sa.Double(), nullable=True))
    op.add_column("weather", sa.Column("humidity", sa.Integer(), nullable=True))
    op.add_column("weather", sa.Column("cloud", sa.Integer(), nullable=True))

    # Корельовані підзапити — єдиний синтаксис UPDATE, однаковий для обох СУБД
    for col in ("precip_mm", "precip_in", "humidity", "cloud"):
        op.execute(
            f"UPDATE weather SET {col} = "
            f"(SELECT p.{col} FROM precipitation p WHERE p.weather_id = weather.id)"
        )

    op.alter_column("weather", "precip_mm", existing_type=sa.Double(), nullable=False)
    op.alter_column("weather", "precip_in", existing_type=sa.Double(), nullable=False)
    op.alter_column("weather", "humidity", existing_type=sa.Integer(), nullable=False)
    op.alter_column("weather", "cloud", existing_type=sa.Integer(), nullable=False)
    op.drop_table("precipitation")
