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


class CurrentMessage(ModelBase):
    __tablename__ = "current_message"
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer)
    image_id: Mapped[int] = mapped_column(Integer)
    send_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='发送时间')
    pending: Mapped[bool] = mapped_column(Boolean, comment="是否有正在进行的原图请求")
    downloaded: Mapped[bool] = mapped_column(Boolean)

    def __init__(self, chat_id, message_id, image_id, **kw):
        super().__init__(**kw)
        self.chat_id = chat_id
        self.message_id = message_id
        self.image_id = image_id
        self.pending = False
        self.downloaded = False
