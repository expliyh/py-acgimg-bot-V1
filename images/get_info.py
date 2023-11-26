import os

from database import *

__path = 'tmp/'

async def get_image_info(image_id: int) -> ImageInfo:
    info = await database.get_image_info_by_id(image_id)
    return info

def get_size(filename):
    # 获取文件大小，单位：KB
    size = os.path.getsize(filename)
    return size / 1024
