from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from config import config


class engine:
    def __init__(self):
        self.engine = None

    def create(self):
        url = f"mariadb+asyncmy://{config.db_username}:{config.db_password}@{config.db_host}:{config.db_name}/{config.db_name}?charset=utf8mb4"
        self.engine = create_async_engine(
            url,
            echo=True,
            echo_pool=True
        )
