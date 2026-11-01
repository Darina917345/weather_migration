"ЕТАП 3: додати булеву колонку precipitation.go_outside"
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

PRECIP_MAX_MM = 0.5
HUMIDITY_MAX = 90

def upgrade() -> None:
    # КРОК 1: колонка поки що може бути порожньою
    op.add_column("precipitation", sa.Column("go_outside", sa.Boolean(), nullable=True))

    # КРОК 2: заповнення одним UPDATE у самій БД.
    # Конструкція sa.case() генерує однаковий CASE WHEN для PostgreSQL і MySQL.
    p = sa.table(
        "precipitation",
        sa.column("precip_mm", sa.Double()),
        sa.column("humidity", sa.Integer()),
        sa.column("go_outside", sa.Boolean()),
    )
    op.execute(
        p.update().values(
            go_outside=sa.case(
                (sa.and_(p.c.precip_mm < PRECIP_MAX_MM, p.c.humidity < HUMIDITY_MAX), sa.true()),
                else_=sa.false(),
            )
        )
    )

    # КРОК 3: тепер порожніх немає - можна вимагати NOT NULL.
    # server_default=false: консервативне значення «ні», якщо хтось вставить рядок, не вказавши його 
    op.alter_column(
        "precipitation", "go_outside",
        existing_type=sa.Boolean(), nullable=False, server_default=sa.false(),
    )

def downgrade() -> None:
    op.drop_column("precipitation", "go_outside")
