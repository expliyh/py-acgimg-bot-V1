# coding=utf-8
from __future__ import unicode_literals, absolute_import

import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, TIMESTAMP, text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class ModelBase(DeclarativeBase):
    pass


class ImageInfo(ModelBase):
    __tablename__ = "image_info"
    image_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(Text)
    helloimg_link: Mapped[str] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    pixiv_id: Mapped[int] = mapped_column(BigInteger)
    author_id: Mapped[int] = mapped_column(BigInteger)
    sap_ori: Mapped[bool] = mapped_column(Boolean,
                                          comment="由于原图超出Telegram的限制而额外存放一份经过压缩的图片，压缩的图片后加-compressed")
    tags: Mapped[str] = mapped_column(LONGTEXT)
    caption: Mapped[str] = mapped_column(Text, comment="作品注释")
    original_url: Mapped[str] = mapped_column(Text, comment="原图(png)的url", nullable=True)
    raw_reply: Mapped[str] = mapped_column(LONGTEXT, comment="PixivAPI返回的原始值")

    # last_update: Mapped[datetime] = mapped_column(DateTime, server_default=func.now, server_onupdate=func.now)

    def get_pixiv_link(self):
        return 'https://www.pixiv.net/artworks/' + str(self.pixiv_id)

    def get_author_link(self):
        return 'https://www.pixiv.net/users/' + str(self.author_id)
