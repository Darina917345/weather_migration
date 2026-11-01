"Налаштування оточення Alembic та підключення до БД."

from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine
from app.config import get_database_url
from app.persistence.base import Base
import app.persistence.models  # noqa: F401  (реєструє моделі в Base.metadata)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _url() -> str:
    x = context.get_x_argument(as_dictionary=True)
    if x.get("db_url"):
        return x["db_url"]
    ini = config.get_main_option("sqlalchemy.url")
    if ini and not ini.startswith("driver://"):
        return ini
    return get_database_url()

def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    engine = create_engine(_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
