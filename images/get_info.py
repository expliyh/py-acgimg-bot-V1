from database import *


async def get_image_info(image_id: int) -> ImageInfo:
    info = await database.get_image_info_by_id(image_id)
    return info
