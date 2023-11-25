import os.path

import aiofiles
import asyncio
from urllib.parse import urlparse

import aiohttp

import database as db_class
from database import *

__tasks = dict()
__path = 'tmp/'

__session = aiohttp.ClientSession()


class FailedToDownload(Exception):
    def __init__(self, code: int, msg: str = None):
        super()
        self.code = code
        self.message = msg


async def __download_file(id: int, path: str, ori: bool = False):
    img_info = await database.get_image_info_by_id(id)
    if img_info.sap_ori:
        if img_info.original_url is None:
            a = urlparse(img_info.link)
            dir_name, base_name = os.path.split(a.path)
            fn, ext = os.path.split(base_name)
            img_info.original_url = dir_name + fn + '.png'

    if ori and img_info.sap_ori:
        link = img_info.original_url
    else:
        link = img_info.link

    global __session

    cnt = 0
    cnt_max = 5
    code = -1
    file_byte = None
    while 0 <= cnt < cnt_max:
        try:
            async with __session.get(link) as response:
                code = response.status
                match response.status:
                    case 200:
                        cnt = -100
                        file_byte = await response.read()
                    case _:
                        cnt += 1
                response.close()
        except aiohttp.ClientError:
            cnt += 1

    if cnt >= cnt_max:
        if os.path.exists(path):
            os.remove(path)
        raise FailedToDownload(code)

    file = await aiofiles.open(path, mode="+wb")
    await file.write(file_byte)
    await file.close()
    return


async def get_origin(id: int):
    lock_id = 'ori_' + str(id)
    lock: asyncio.Lock | None = __tasks.get(lock_id)
    if lock is not None and lock.locked():
        await lock.acquire()
        lock.release()
    path = __path + lock_id
    if os.path.exists(path):
        return await aiofiles.open(path, 'rb')
    else:
        if __tasks.get(lock_id) is None:
            __tasks[lock_id] = asyncio.Lock()
        await __tasks[lock_id].acquire()
        await __download_file(id, path, True)
        __tasks[lock_id].release()

    return await aiofiles.open(path, 'rb')


async def get_image(id: int):
    lock_id = 'img_' + str(id)
    lock: asyncio.Lock | None = __tasks.get('img_' + str(id))
    if lock is not None and lock.locked():
        await lock.acquire()
        lock.release()
    path = __path + 'img_' + str(id)
    if os.path.exists(path):
        return await aiofiles.open(path, 'rb')
    else:
        if __tasks.get(lock_id) is None:
            __tasks[lock_id] = asyncio.Lock()
        await __tasks[lock_id].acquire()
        await __download_file(id, path, False)
        __tasks[lock_id].release()

    return await aiofiles.open(path, 'rb')
