from copy import copy

from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession

from sqlalchemy import select, update, create_engine, func, delete
from sqlalchemy.dialects.mysql import insert
import asyncmy
from config import config
from . import imginfo
from . import current_message
from . import illustinfo
from . import database_config
from .imginfo import ImageInfo
from .current_message import CurrentMessage
from .illustinfo import IllustInfo
from .database_config import DatabaseConfig


def get_none_async_engine():
    url = f"mariadb+pymysql://{config.db_username}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}?charset=utf8mb4"
    none_async_engine = create_engine(
        url,
        echo=True,
        echo_pool=True,
        pool_recycle=3600
    )
    return none_async_engine


class engine:
    def __init__(self):
        self.engine = None

    def create(self):
        url = f"mariadb+asyncmy://{config.db_username}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}?charset=utf8mb4"
        self.engine = create_async_engine(
            url,
            echo=True,
            echo_pool=True,
            pool_recycle=3600
        )

    def new_session(self) -> async_sessionmaker[AsyncSession]:
        async_session = async_sessionmaker(self.engine)
        return async_session

    def new_session_no_expire_on_commit(self) -> async_sessionmaker[AsyncSession]:
        async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        return async_session

    async def get_image_info_by_id(self, image_id: int) -> ImageInfo:
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(ImageInfo).filter(ImageInfo.image_id == image_id))
            img_info = result.scalars().first()

        return img_info

    async def get_image_info_by_pixiv_id(self, pixiv_id: int):
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(ImageInfo).filter(ImageInfo.pixiv_id == pixiv_id))
            img_info = result.scalars().first()

        return img_info

    async def add_link_and_filename_by_pixiv_id(self, pixiv_id: int, link: str, filename: str):
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(ImageInfo).filter(ImageInfo.pixiv_id == pixiv_id))
            img_info = result.scalars().first()
            filenames: list = img_info.filenames
            links: list = img_info.links
            filenames.append(filename)
            links.append(link)
            update_stmt = update(ImageInfo).where(ImageInfo.pixiv_id == pixiv_id).values(
                links=links,
                filenames=filenames
            )
            await session.execute(update_stmt)
            await session.commit()
            await session.close()
        return

    async def add_image_info(self, image_info: ImageInfo):
        async_session = self.new_session_no_expire_on_commit()
        async with async_session() as session:
            session.add(image_info)
            await session.commit()
            new_id = image_info.image_id
        return new_id

    async def get_max_image_id(self):
        async_session = self.new_session()
        async with async_session() as session:
            max_id = (await session.execute(func.max(ImageInfo.image_id))).scalars().first()
        return max_id

    async def get_current_message_by_chat_id(self, chat_id: int) -> CurrentMessage | None:
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(CurrentMessage).filter(CurrentMessage.chat_id == chat_id))
            current_message = result.scalars().first()

        return current_message

    async def set_config(self, what, detail: dict):
        async_session = self.new_session()
        async with async_session() as session:
            insert_stmt = insert(DatabaseConfig).values(
                what=what,
                detail=detail
            )
            update_stmt = insert_stmt.on_duplicate_key_update(
                detail=detail
            )
            await session.execute(update_stmt)
            await session.commit()
            await session.close()
        return

    async def get_config(self, what) -> dict | None:
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(DatabaseConfig).filter(DatabaseConfig.what == what))
            tmp = result.scalars().first()
            if tmp is None:
                return None
            resp = copy(tmp.detail)
        return resp

    async def delete_config(self, what) -> None:
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(delete(DatabaseConfig).where(DatabaseConfig.what == what))
            await session.commit()
            await session.close()
        return

    async def add_current_message(self, current_message: CurrentMessage):
        async_session = self.new_session()
        async with async_session() as session:
            session.add(current_message)
            await session.commit()
            await session.close()
        return

    async def update_current_message(self, current_message: CurrentMessage):
        async_session = self.new_session()
        async with async_session() as session:
            insert_stmt = insert(CurrentMessage).values(
                chat_id=current_message.chat_id,
                message_id=current_message.message_id,
                image_id=current_message.image_id,
                sub_id=current_message.sub_id,
                pending=False,
                downloaded=False
            )
            update_stmt = insert_stmt.on_duplicate_key_update(
                message_id=current_message.message_id,
                image_id=current_message.image_id,
                sub_id=current_message.sub_id,
                send_time=func.current_timestamp(),
                pending=False,
                downloaded=False
            )
            await session.execute(update_stmt)
            await session.commit()
            await session.close()
        return

    async def set_pending(self, chat_id: int, pending: bool):
        async_session = self.new_session()
        async with async_session() as session:
            await session.execute(update(CurrentMessage).values(pending=pending))
            await session.commit()
            await session.close()
        return

    async def add_illust_info(self, illust_info: ImageInfo):
        async_session = self.new_session()
        async with async_session() as session:
            session.add(illust_info)
            await session.commit()
            await session.close()
        return

    async def get_illust_info_by_pixiv_id(self, pixiv_id: int) -> IllustInfo | None:
        async_session = self.new_session()
        async with async_session() as session:
            result = await session.execute(select(IllustInfo).filter(IllustInfo.pixiv_id == pixiv_id))
            illust_info = result.scalars().first()
        try:
            if int(illust_info.pixiv_id) != pixiv_id:
                return None
        except AttributeError:
            return None
        return illust_info


database = engine()


def create_table():
    imginfo.ModelBase.metadata.create_all(get_none_async_engine())
    current_message.ModelBase.metadata.create_all(get_none_async_engine())
    illustinfo.ModelBase.metadata.create_all(get_none_async_engine())
    database_config.ModelBase.metadata.create_all(get_none_async_engine())
