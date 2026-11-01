"Шар Repository: єдине місце, яке розмовляє з БД через ORM"
import datetime as dt
from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.persistence.models import Precipitation, Weather

class WeatherRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, rows: Sequence[Weather]) -> None:
        self.session.add_all(rows)
        self.session.flush()  # відправляє INSERT-и в БД, але ще не commit

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Weather)) or 0

    def find(
        self,
        country: str,
        day: dt.date,
        location: str | None = None,
        go_outside: bool | None = None,
    ) -> list[Weather]:
        """Погода за країною й датою (+ необов'язково місто та відповідь «виходити?»)."""
        start = dt.datetime.combine(day, dt.time.min)
        end = start + dt.timedelta(days=1)

        stmt = (
            select(Weather)
            # joinedload: забрати погоду і опади одним запитом (JOIN), а не робити по додатковому запиту на кожен рядок
            .options(joinedload(Weather.precipitation))
            .join(Weather.precipitation)
            # lower() з обох боків: у PostgreSQL порівняння рядків чутливе до регістру, а в MySQL — ні. Так поведінка однакова на обох базах.
            .where(func.lower(Weather.country) == country.strip().lower())
            # діапазон [початок дня; початок наступного) замість "дата == день":
            # так працює індекс і не треба обрізати час у колонці
            .where(Weather.last_updated >= start, Weather.last_updated < end)
            .order_by(Weather.location_name, Weather.last_updated)
        )
        if location:
            stmt = stmt.where(func.lower(Weather.location_name) == location.strip().lower())
        if go_outside is not None:
            stmt = stmt.where(Precipitation.go_outside.is_(go_outside))
        return list(self.session.scalars(stmt).unique())

    def countries(self) -> list[str]:
        return list(self.session.scalars(select(Weather.country).distinct().order_by(Weather.country)))

    def date_range(self) -> tuple[dt.datetime, dt.datetime] | None:
        row = self.session.execute(
            select(func.min(Weather.last_updated), func.max(Weather.last_updated))
        ).one()
        return None if row[0] is None else (row[0], row[1])
