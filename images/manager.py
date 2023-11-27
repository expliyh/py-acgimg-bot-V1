import os.path

import aiofiles
import asyncio
from urllib.parse import urlparse

import aiohttp

from .get_info import get_size, __path
from .compress import auto_compress_for_telegram_photo

import database as db_class
from database import *

__tasks = dict()

__session = aiohttp.ClientSession()


class FailedToDownload(Exception):
    def __init__(self, code: int, msg: str = None):
        super()
        self.code = code
        self.message = msg


async def __download_file(image_id: int, sub_id: int):
    img_info = await database.get_image_info_by_id(image_id)
    # if img_info.sap_ori:
    #     a = urlparse(img_info.link)
    #     dir_name, base_name = os.path.split(a.path)
    #     fn, ext = os.path.split(base_name)

    path = __path + img_info.filenames[sub_id]

    global __session

    cnt = 0
    cnt_max = 5
    code = -1
    file_byte = None
    while 0 <= cnt < cnt_max:
        try:
            async with __session.get(img_info.links[sub_id]) as response:
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


async def __download_file_old(image_id: int, path: str, ori: bool = False):
    img_info = await database.get_image_info_by_id(image_id)
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


async def get_origin(image_id: int, sub_id: int):
    image_info = await database.get_image_info_by_id(image_id)
    lock_id = 'img_' + str(image_id)
    lock: asyncio.Lock | None = __tasks.get('img_' + str(image_id))
    if lock is None:
        __tasks['img_' + str(image_id)] = asyncio.Lock()
    await __tasks['img_' + str(image_id)].acquire()
    path = __path + image_info.filename
    send_path = None
    if not os.path.exists(path):
        await __download_file(image_id, sub_id)
    __tasks['img_' + str(image_id)].release()
    return await aiofiles.open(path, 'rb')


async def get_origin_old(id: int):
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
        await __download_file_old(id, path, True)
        __tasks[lock_id].release()

    return await aiofiles.open(path, 'rb')


async def get_image(image_id: int, sub_id: int):
    image_info = await database.get_image_info_by_id(image_id)
    lock_id = 'img_' + str(image_id)
    lock: asyncio.Lock | None = __tasks.get('img_' + str(image_id))
    if lock is None:
        __tasks['img_' + str(image_id)] = asyncio.Lock()
        lock: asyncio.Lock = __tasks.get('img_' + str(image_id))
    await __tasks['img_' + str(image_id)].acquire()
    path = __path + image_info.filenames[sub_id]
    send_path = None
    if not os.path.exists(path):
        await __download_file(image_id, sub_id)
    if os.path.exists(path):
        if get_size(path) > 9000:
            compressed_path = f"{__path}compressed_{str(image_id)}_{str(sub_id)}.jpg"
            if not os.path.exists(compressed_path):
                auto_compress_for_telegram_photo(path, image_id, sub_id)
            send_path = compressed_path
        else:
            send_path = path
    __tasks['img_' + str(image_id)].release()
    return await aiofiles.open(send_path, 'rb')


async def get_image_old(id: int):
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
        await __download_file_old(id, path, False)
        __tasks[lock_id].release()

    return await aiofiles.open(path, 'rb')
