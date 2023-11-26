from datetime import datetime

from database import IllustInfo

from singleton_class_decorator import *


class CachedIllustDetail:
    pixiv_id: int
    title: str
    caption: str
    author_name: str
    author_id: int
    tags: dict
    page_count: int
    sanity_level: int
    x_restrict: int
    meta_single_page: dict
    meta_pages: dict
    illust_ai_type: int
    last_update: datetime
    cached_time: datetime
    call_cnt: int

    def __init__(self, database_illust_detail: IllustInfo = None):
        if database_illust_detail is not None:
            self.pixiv_id = database_illust_detail.pixiv_id
            self.title = database_illust_detail.title
            self.caption = database_illust_detail.caption
            self.author_name = database_illust_detail.author_name
            self.author_id = database_illust_detail.author_id
            self.tags = database_illust_detail.tags
            self.page_count = database_illust_detail.page_count
            self.sanity_level = database_illust_detail.sanity_level
            self.x_restrict = database_illust_detail.x_restrict
            self.meta_single_page = database_illust_detail.meta_single_page
            self.meta_pages = database_illust_detail.meta_pages
            self.illust_ai_type = database_illust_detail.illust_ai_type
            self.last_update = database_illust_detail.last_update
            self.cached_time = datetime.now()
            self.call_cnt = 0


@singleton
class IllustDetailCache:

    def __init__(self, max_size: int = 512, expire_time: int = 300, check_interval: int = 60):
        self.__cache: dict = {}
        self.__max_size = max_size
        self.__expire_time = expire_time
        self.check_inverval = check_interval
