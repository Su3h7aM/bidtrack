import os
from sqlmodel import SQLModel # Although we directly use models.SQLModel.metadata
from src.db import models # To access SQLModel.metadata via models.SQLModel.metadata
# Import DATABASE_URL from your project's database configuration
# This allows Alembic to use the same database URL as your application
from src.db.database import DATABASE_URL as APP_DATABASE_URL

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = models.SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get the database URL from environment variable or alembic.ini
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        # As a final fallback, try the imported APP_DATABASE_URL if it's not None
        # This covers cases where DATABASE_URL env var might not be set when alembic runs
        # but was set when the app was configured.
        if APP_DATABASE_URL:
            db_url = APP_DATABASE_URL
        else:
            raise ValueError("Database URL cannot be determined. Set DATABASE_URL environment variable or ensure sqlalchemy.url in alembic.ini is correct.")

    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database URL from environment variable or alembic.ini
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        # As a final fallback, try the imported APP_DATABASE_URL if it's not None
        if APP_DATABASE_URL:
            db_url = APP_DATABASE_URL
        else:
            raise ValueError("Database URL cannot be determined. Set DATABASE_URL environment variable or ensure sqlalchemy.url in alembic.ini is correct.")

    # Create a new engine configuration dictionary
    engine_config = config.get_section(config.config_ini_section, {})
    engine_config['sqlalchemy.url'] = db_url

    connectable = engine_from_config(
        engine_config, # Use the modified config with the correct URL
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
