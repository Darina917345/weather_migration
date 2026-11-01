"ORM-моделі (шар Persistence)"
import datetime as dt
import enum
from sqlalchemy import Boolean, DateTime, Double, Enum, ForeignKey, Index, Integer, String, Time, UniqueConstraint
from sqlalchemy import false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.persistence.base import Base

class WindDirection(str, enum.Enum):
    """16 румбів вітру. Поле з обмеженим набором значень = enumeration."""
    N = "N"
    NNE = "NNE"
    NE = "NE"
    ENE = "ENE"
    E = "E"
    ESE = "ESE"
    SE = "SE"
    SSE = "SSE"
    S = "S"
    SSW = "SSW"
    SW = "SW"
    WSW = "WSW"
    W = "W"
    WNW = "WNW"
    NW = "NW"
    NNW = "NNW"

class Weather(Base):
    __tablename__ = "weather"
    __table_args__ = (Index("ix_weather_country_last_updated", "country", "last_updated"),)
    id: Mapped[int] = mapped_column(primary_key=True)

    country: Mapped[str] = mapped_column(String(100))                  # текст
    wind_degree: Mapped[int] = mapped_column(Integer)                  # ціле число
    wind_kph: Mapped[float] = mapped_column(Double)                    # дробове число
    wind_direction: Mapped[WindDirection] = mapped_column(             # enumeration
        Enum(WindDirection, name="wind_direction_enum",
             values_callable=lambda e: [m.value for m in e])
    )
    last_updated: Mapped[dt.datetime] = mapped_column(DateTime)        # дата (+час)
    sunrise: Mapped[dt.time | None] = mapped_column(Time, nullable=True)  # час

    # Допоміжні колонки
    location_name: Mapped[str] = mapped_column(String(150))
    condition_text: Mapped[str] = mapped_column(String(100))
    temperature_celsius: Mapped[float] = mapped_column(Double)

    # зв'язок з таблицею опадів (1:1). Сама таблиця описана нижче.
    precipitation: Mapped["Precipitation"] = relationship(
        back_populates="weather", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )

class Precipitation(Base):
    """Категорія №3 «Опади» — окрема таблиця."""
    __tablename__ = "precipitation"
    __table_args__ = (UniqueConstraint("weather_id", name="uq_precipitation_weather_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    weather_id: Mapped[int] = mapped_column(
        ForeignKey("weather.id", ondelete="CASCADE", name="fk_precipitation_weather_id_weather")
    )
    precip_mm: Mapped[float] = mapped_column(Double)
    precip_in: Mapped[float] = mapped_column(Double)
    humidity: Mapped[int] = mapped_column(Integer)
    cloud: Mapped[int] = mapped_column(Integer)
    # «Чи варто виходити на вулицю»: True = так, False = ні.
    # server_default — значення, яке підставляє сама бд, якщо не вказано нічого.
    go_outside: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    weather: Mapped[Weather] = relationship(back_populates="precipitation")
