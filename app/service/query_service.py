"""Шар Service: пошук погоди для користувача.

Повертає прості dataclass-и (WeatherReport), а не ORM-об'єкти. Тоді шар
Presentation нічого не знає про SQLAlchemy і про таблиці: якщо завтра ми
змінимо структуру БД, інтерфейс не доведеться переписувати.
"""
import datetime as dt
from dataclasses import dataclass
from app.repository.weather_repository import WeatherRepository

@dataclass(frozen=True)
class WeatherReport:
    country: str
    location_name: str
    last_updated: dt.datetime
    condition_text: str
    temperature_celsius: float
    wind_kph: float
    wind_degree: int
    wind_direction: str
    sunrise: dt.time | None
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    go_outside: bool

class WeatherQueryService:
    def __init__(self, repository: WeatherRepository):
        self.repo = repository

    def search(
        self,
        country: str,
        day: dt.date,
        location: str | None = None,
        go_outside: bool | None = None,
    ) -> list[WeatherReport]:
        if not country or not country.strip():
            raise ValueError("Країну потрібно вказати")
        rows = self.repo.find(country, day, location, go_outside)
        return [
            WeatherReport(
                country=w.country,
                location_name=w.location_name,
                last_updated=w.last_updated,
                condition_text=w.condition_text,
                temperature_celsius=w.temperature_celsius,
                wind_kph=w.wind_kph,
                wind_degree=w.wind_degree,
                wind_direction=w.wind_direction.value,
                sunrise=w.sunrise,
                precip_mm=w.precipitation.precip_mm,
                precip_in=w.precipitation.precip_in,
                humidity=w.precipitation.humidity,
                cloud=w.precipitation.cloud,
                go_outside=w.precipitation.go_outside,
            )
            for w in rows
        ]

    def available(self) -> tuple[list[str], tuple[dt.datetime, dt.datetime] | None]:
        return self.repo.countries(), self.repo.date_range()
