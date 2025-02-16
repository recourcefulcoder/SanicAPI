import config

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


url_object = URL.create(
    "postgresql+asyncpg",
    username=config.POSTGRES_USER,
    password=config.POSTGRES_PASSWORD,
    host=config.HOST,
    database=config.POSTGRES_DB,
)
engine = create_async_engine(url_object, poolclass=NullPool)
