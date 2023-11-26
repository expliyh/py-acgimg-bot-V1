from pixivpy3 import *
from config import config
from singleton_class_decorator import singleton
from database import database
from database import IllustInfo
from .illust_detail_cache import *


@singleton
class PixivAPI:
    def __init__(self):
        self.enable = True
        if config.pixiv_token is None or config.pixiv_token == '':
            self.__api = None
            if config.py_api_url is None or config.py_api_url == '':
                self.enable = False
        else:
            self.__api = AppPixivAPI()

        if self.__api is not None:
            self.__api.auth(refresh_token=config.pixiv_token)

        self.__cache = IllustDetailCache()

    async def get_illust_info_by_pixiv_id(self, pixiv_id: int, force_refresh=False, force_deep_refresh=False):
        illust_info = None
        if not force_refresh:
            illust_info = self.__cache.get_cache_by_pixiv_id(pixiv_id)
        if illust_info is None:
            illust_info = CachedIllustDetail(await database.get_illust_info_by_pixiv_id(pixiv_id))
            try:
                illust_info.pixiv_id = illust_info.pixiv_id
                self.__cache.update_cache(await database.get_illust_info_by_pixiv_id(pixiv_id))
            except AttributeError as ex:
                illust_info = None
                pass
        if illust_info is None:
            illust_info_dict: dict = self.__api.illust_detail(pixiv_id)
            db_illust_info = IllustInfo(illust_info_dict)
            self.__cache.update_cache(db_illust_info)
            illust_info = CachedIllustDetail(db_illust_info)
        else:
            pass
        return illust_info
