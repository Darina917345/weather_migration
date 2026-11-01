"Шар Presentation: консольний інтерфейс. Лише розбір аргументів і друк."
import argparse
import datetime as dt
import sys
from app.persistence.database import make_engine, session_scope
from app.repository.weather_repository import WeatherRepository
from app.service.import_service import ImportService
from app.service.query_service import WeatherQueryService, WeatherReport


def cmd_import(args) -> int:
    engine = make_engine(args.db_url)
    with session_scope(engine) as session:
        repo = WeatherRepository(session)
        if repo.count() and not args.append:
            print("У таблиці вже є дані. Додайте --append, щоб дозавантажити.")
            return 1
        report = ImportService(repo).import_csv(args.csv)
    print(f"Прочитано рядків: {report.total}")
    print(f"Завантажено:      {report.imported}")
    for reason, n in report.rejected.items():
        print(f"Відхилено ({reason}): {n}")
    return 0

def _print_report(r: WeatherReport) -> None:
    yn = "ТАК" if r.go_outside else "НІ"
    print(f"{r.country} — {r.location_name}  ({r.last_updated:%Y-%m-%d %H:%M})")
    print(f"  Стан:             {r.condition_text}, {r.temperature_celsius:.1f} °C")
    print(f"  Вітер:            {r.wind_kph} км/год, {r.wind_degree}° ({r.wind_direction})")
    print(f"  Схід сонця:       {r.sunrise.strftime('%H:%M') if r.sunrise else 'немає даних'}")
    print(f"  Опади:            {r.precip_mm} мм ({r.precip_in} дюйма)")
    print(f"  Вологість/хмари:  {r.humidity}% / {r.cloud}%")
    print(f"  Чи варто виходити на вулицю: {yn}")
    print()

def cmd_search(args) -> int:
    try:
        day = dt.date.fromisoformat(args.date)
    except ValueError:
        print("Дата має бути у форматі РРРР-ММ-ДД, наприклад 2026-10-15")
        return 2
    go = {"yes": True, "no": False, None: None}[args.go_outside]
    engine = make_engine(args.db_url)
    with session_scope(engine) as session:
        service = WeatherQueryService(WeatherRepository(session))
        try:
            reports = service.search(args.country, day, args.location, go)
        except ValueError as exc:
            print(exc)
            return 2
    if not reports:
        print("Нічого не знайдено. Перевірте країну/дату командою `countries`.")
        return 1
    for r in reports:
        _print_report(r)
    print(f"Знайдено записів: {len(reports)}")
    return 0

def cmd_countries(args) -> int:
    engine = make_engine(args.db_url)
    with session_scope(engine) as session:
        countries, rng = WeatherQueryService(WeatherRepository(session)).available()
    if rng:
        print(f"Дати в базі: {rng[0]:%Y-%m-%d} … {rng[1]:%Y-%m-%d}")
    print("Країни: " + ", ".join(countries))
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="weather", description="Погодна БД")
    p.add_argument("--db-url", help="Рядок підключення (інакше береться DATABASE_URL)")
    sub = p.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-csv", help="Завантажити CSV у БД")
    imp.add_argument("csv", help="Шлях до GlobalWeatherRepository.csv")
    imp.add_argument("--append", action="store_true", help="Дозволити завантаження в непорожню таблицю")
    imp.set_defaults(func=cmd_import)
    se = sub.add_parser("search", help="Знайти погоду за країною та датою")
    se.add_argument("--country", required=True, help="Країна, напр. Ukraine")
    se.add_argument("--date", required=True, help="Дата РРРР-ММ-ДД")
    se.add_argument("--location", help="(необов'язково) місто, напр. Kyiv")
    se.add_argument("--go-outside", choices=["yes", "no"], help="(необов'язково) лише де можна/не можна виходити")
    se.set_defaults(func=cmd_search)
    co = sub.add_parser("countries", help="Які країни та дати є в базі")
    co.set_defaults(func=cmd_countries)
    return p

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
