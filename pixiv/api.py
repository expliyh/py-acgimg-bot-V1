from pixivpy3 import *
from config import config
from singleton_class_decorator import singleton
from database import database
from database import IllustInfo


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

    def get_illust_info_by_pixiv_id(self, pixiv_id: int, force_refresh=False, force_deep_refresh=False):
        if not force_refresh:

