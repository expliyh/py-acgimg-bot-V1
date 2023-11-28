import asyncio
from abc import abstractmethod
from singleton_class_decorator import singleton
from database import database
from configs import BackblazeConfig

import nest_asyncio

from .backblaze import Backblaze

nest_asyncio.apply()


@singleton
class ImageBed:

    def __init__(self):
        self.bed: Backblaze | None = None

    def upload_image(self, file_name: str, document: bytes) -> str:
        """
        上传内存中的图片并获取链接
        :param file_name: 文件名
        :param document: bytes形式的图片
        :return: 图片的链接
        """
        return self.bed.upload_image(file_name, document)

    def init_image_bed(self):
        loop = asyncio.get_event_loop()
        bed_config = loop.run_until_complete(database.get_config("img_bed"))
        if bed_config is None:
            self.bed = None
            return
        match bed_config['description']:
            case None:
                self.bed = None
                return
            case "BackBlaze":
                config = BackblazeConfig()
                config.__dict__.update(bed_config)
                self.bed = Backblaze(conf=config)
                return


image_bed = ImageBed()
