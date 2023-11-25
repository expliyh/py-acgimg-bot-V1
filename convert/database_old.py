import logging

import aiomysql
import asyncio
from config import config
from aiomysql.cursors import DictCursor
from .ImageQueue import ImageQueue


class Database:

    async def is_downloaded(self, chat_id: int) -> bool | None:
        sql = 'SELECT `downloaded` FROM `py_queue` WHERE `chat_id`=%s'
        params = (chat_id,)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                result = await cursor.fetchone()

        if result is None:
            return None
        return result[0] != 0

    async def set_pending(self, chat_id: int, status: bool):
        sql = 'UPDATE `py_queue` SET `pending`=%s WHERE `chat_id`=%s'
        params = (status, chat_id)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
        return

    async def get_queue(self, chat_id: int) -> ImageQueue | None:
        sql = 'SELECT `chat_id`, `message_id`, `image_id`, `timestamp`, `pending`, `downloaded` FROM `py_queue` WHERE `chat_id` = %s'
        params = (chat_id,)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                result = await cursor.fetchone()

        logging.info(result)
        if result is None:
            return None
        return ImageQueue(result[0], result[1], result[2], result[4] != 0, result[5] != 0)

    async def is_pending(self, chat_id: int) -> bool | None:
        sql = 'SELECT `pending` FROM `py_queue` WHERE `chat_id` = %s'
        params = (chat_id,)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                result = await cursor.fetchone()

        logging.info(result)
        if result is None:
            return None
        else:
            if result[0] == 0:
                return False
            else:
                return True

    async def in_queue(self, chat_id: int, message_id: int) -> int | None:
        sql = 'SELECT `image_id` FROM `py_queue` WHERE `chat_id` = %s AND `message_id` = %s'
        params = (chat_id, message_id)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                result = await cursor.fetchone()
        if result is None:
            return None
        else:
            return result[0]

    async def update_queue(self, chat_id: int, message_id: int, image_id: int):
        sql = 'INSERT INTO `py_queue`(`chat_id`, `message_id`, `image_id`, `pending`) VALUES (%s,%s,%s,%s) ON ' \
              'DUPLICATE KEY UPDATE `chat_id` = %s, `message_id` = %s, `image_id` = %s, `pending` = %s;'
        params = (chat_id, message_id, image_id, False, chat_id, message_id, image_id, False)
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)

    async def get_by_id(self, what: tuple, id: int):
        sql = 'SELECT * FROM `imginfo` WHERE `id` = %s'
        params = (id,)
        async with self.pool.acquire() as connection:
            async with connection.cursor(DictCursor) as cursor:
                await cursor.execute(sql, params)
                result: dict = await cursor.fetchone()
        dict_result = dict()
        for i in what:
            dict_result[i] = result.get(i)
        return dict_result

    async def get_max_id(self):
        sql = "SELECT MAX(id) FROM `imginfo` WHERE 1"
        return (await self.execute(sql))[0][0]

    async def execute(self, sql: str, params: tuple = None) -> None | str | int | tuple:
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(sql, params)
                results = await cursor.fetchall()
                return results

    def create_pool(self):
        loop = asyncio.get_event_loop()
        self.pool: aiomysql.Pool = loop.run_until_complete(aiomysql.create_pool(
            host=config.db_host,
            port=config.db_port,
            user=config.db_username,
            password=config.db_password,
            db=config.db_name,
            charset='utf8mb4',
            autocommit=True,
            maxsize=10,
            minsize=1,
            loop=loop
        ))

    def __init__(self):
        self.pool = None


db = Database()
