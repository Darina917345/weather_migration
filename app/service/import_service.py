"Шар Service: бізнес-логіка. Тут - читання CSV та перетворення в ORM-об'єкти"
import datetime as dt
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
from app.persistence.models import Precipitation, Weather, WindDirection
from app.repository.weather_repository import WeatherRepository
from app.service.outdoor_rules import should_go_outside

# колонки CSV, які ми використовуються
CSV_COLUMNS = [
    "country", "location_name", "last_updated", "condition_text",
    "temperature_celsius", "wind_kph", "wind_degree", "wind_direction",
    "sunrise", "precip_mm", "precip_in", "humidity", "cloud",
]

@dataclass
class ImportReport:
    total: int = 0
    imported: int = 0
    rejected: Counter = field(default_factory=Counter)

    @property
    def rejected_total(self) -> int:
        return sum(self.rejected.values())

def _is_missing(v) -> bool:
    # pandas позначає порожні клітинки як NaN; NaN у БД потрапляти не повинен
    return v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA

def _parse_sunrise(value) -> dt.time | None:
    """'05:45 AM' -> time(5, 45). Некоректні значення ('No sunrise') -> None."""
    if _is_missing(value):
        return None
    try:
        return dt.datetime.strptime(str(value).strip(), "%I:%M %p").time()
    except ValueError:
        return None

class ImportService:
    def __init__(self, repository: WeatherRepository):
        self.repo = repository

    def import_csv(self, path: str | Path, chunk_size: int = 5000) -> ImportReport:
        header = pd.read_csv(path, nrows=0).columns
        missing = [c for c in CSV_COLUMNS if c not in header]
        if missing:
            raise ValueError(f"У CSV немає потрібних колонок: {missing}")

        report = ImportReport()
        # chunksize: файл читається шматками, щоб не тримати все в пам'яті
        for chunk in pd.read_csv(path, usecols=CSV_COLUMNS, chunksize=chunk_size):
            objects = []
            for rec in chunk.to_dict("records"):
                report.total += 1
                obj, reason = self._to_orm(rec)
                if obj is None:
                    report.rejected[reason] += 1
                else:
                    objects.append(obj)
            self.repo.add_many(objects)
            self.repo.session.commit()  # одна транзакція на шматок
            report.imported += len(objects)
        return report

    @staticmethod
    def _to_orm(rec: dict) -> tuple[Weather | None, str]:
        required = ["country", "location_name", "last_updated", "wind_kph",
                    "wind_degree", "precip_mm", "precip_in", "humidity", "cloud",
                    "temperature_celsius", "condition_text"]
        if any(_is_missing(rec[c]) for c in required):
            return None, "порожнє обов'язкове поле"
        try:
            last_updated = pd.to_datetime(rec["last_updated"]).to_pydatetime()
            direction = WindDirection(str(rec["wind_direction"]).strip())
        except (ValueError, TypeError):
            return None, "некоректна дата або напрям вітру"
        return Weather(
            country=str(rec["country"]).strip(),
            location_name=str(rec["location_name"]).strip(),
            last_updated=last_updated,
            condition_text=str(rec["condition_text"]).strip(),
            temperature_celsius=float(rec["temperature_celsius"]),
            wind_kph=float(rec["wind_kph"]),
            wind_degree=int(rec["wind_degree"]),
            wind_direction=direction,
            sunrise=_parse_sunrise(rec["sunrise"]),
            # дочірній об'єкт: SQLAlchemy сам вставить спочатку weather,візьме її id і підставить у precipitation.weather_id
            precipitation=Precipitation(
                precip_mm=float(rec["precip_mm"]),
                precip_in=float(rec["precip_in"]),
                humidity=int(rec["humidity"]),
                cloud=int(rec["cloud"]),
                go_outside=should_go_outside(float(rec["precip_mm"]), int(rec["humidity"])),
            ),
        ), ""
