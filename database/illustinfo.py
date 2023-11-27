# coding=utf-8
from __future__ import unicode_literals, absolute_import

import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, TIMESTAMP, text, func, JSON
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

import json

from config import config


class ModelBase(DeclarativeBase):
    pass


class IllustInfo(ModelBase):
    __tablename__ = f"{config.db_prefix}pixiv_api_cache"
    pixiv_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(BigInteger)
    tags: Mapped[list] = mapped_column(JSON)
    page_count: Mapped[int] = mapped_column(Integer)
    sanity_level: Mapped[int] = mapped_column(Integer)
    x_restrict: Mapped[int] = mapped_column(Integer)
    meta_single_page: Mapped[dict] = mapped_column(JSON)
    meta_pages: Mapped[list] = mapped_column(JSON)
    illust_ai_type: Mapped[int] = mapped_column(Integer)
    last_update: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def is_r18(self) -> bool:
        if self.sanity_level > 5:
            return True
        else:
            return False

    def __init__(self, illust_detail_in_dict: dict = None, **kw):
        super().__init__(**kw)
        if illust_detail_in_dict is not None:
            try:
                illust = illust_detail_in_dict['illust']
                self.pixiv_id = illust['id']
                self.title = illust['title']
                self.caption = illust['caption']
                user = illust['user']
                self.author_name = user['name']
                self.author_id = user['id']
                self.tags = illust['tags']
                self.page_count = illust['page_count']
                self.sanity_level = illust['sanity_level']
                self.x_restrict = illust['x_restrict']
                self.meta_single_page = illust['meta_single_page']
                self.meta_pages = illust['meta_pages']
                self.illust_ai_type = illust['illust_ai_type']
            except KeyError as ex:
                print(illust_detail_in_dict.__dict__)
