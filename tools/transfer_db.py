"""Перенесення бази з однієї СУБД в іншу: PostgreSQL → MySQL (або навпаки).

Три кроки:
  1) У цільовій базі накочуємо ті самі міграції (alembic upgrade head) -
     вона отримує таку саму структуру, без жодного ручного SQL.
  2) Копіюємо дані таблиця за таблицею (спочатку батьківська `weather`,
     потім дочірня `precipitation`), зберігаючи id, щоб зв'язки не зламались.
  3) Звіряємо обидві бази (tools.verify_databases).

Запуск:
  python -m tools.transfer_db --source "<url звідки>" --target "<url куди>"
"""
import argparse
import sys
from pathlib import Path
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
import app.persistence.models  # noqa: F401
from app.persistence.base import Base
from tools.verify_databases import compare

ROOT = Path(__file__).resolve().parents[1]  # корінь проєкту

def _alembic_cfg(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg

def _fix_postgres_sequences(engine: sa.Engine) -> None:
    """PostgreSQL: після вставки рядків з явним id лічильник (sequence) не знає про них.
    Без цього наступний звичайний INSERT отримає id=1 і впаде на дублікаті.
    (MySQL робить це автоматично — AUTO_INCREMENT сам підтягується.)
    """
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            conn.execute(sa.text(
                f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table.name}), 1), "
                f"(SELECT COUNT(*) > 0 FROM {table.name}))"
            ))

def transfer(source_url: str, target_url: str, batch: int = 5000) -> None:
    src, dst = sa.create_engine(source_url), sa.create_engine(target_url)

    print(f"[1/3] Накочуємо міграції на цільову базу ({dst.dialect.name})...")
    command.upgrade(_alembic_cfg(target_url), "head")

    with dst.connect() as c:
        for table in Base.metadata.sorted_tables:
            if c.execute(sa.select(sa.func.count()).select_from(table)).scalar():
                raise SystemExit(f"Цільова таблиця {table.name} не порожня — перенесення скасовано.")

    print(f"[2/3] Копіюємо дані ({src.dialect.name} → {dst.dialect.name})...")
    # sorted_tables впорядковує за залежностями: батьки раніше за дітей
    for table in Base.metadata.sorted_tables:
        last, total = 0, 0
        while True:
            with src.connect() as sc:
                rows = sc.execute(
                    table.select().where(table.c.id > last).order_by(table.c.id).limit(batch)
                ).mappings().all()
            if not rows:
                break
            with dst.begin() as dc:  # одна транзакція на шматок
                dc.execute(table.insert(), [dict(r) for r in rows])
            last = rows[-1]["id"]
            total += len(rows)
        print(f"      {table.name}: {total} рядків")

    if dst.dialect.name == "postgresql":
        _fix_postgres_sequences(dst)

    print("[3/3] Звіряємо бази...")
    problems = compare(source_url, target_url, batch)
    if problems:
        raise SystemExit("РОЗБІЖНОСТІ:\n" + "\n".join(problems))
    print("Готово: бази ідентичні.")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--source", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--batch", type=int, default=5000)
    args = p.parse_args()
    transfer(args.source, args.target, args.batch)
    return 0

if __name__ == "__main__":
    sys.exit(main())
