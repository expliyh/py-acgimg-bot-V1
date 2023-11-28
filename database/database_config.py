# coding=utf-8
from __future__ import unicode_literals, absolute_import

import datetime
from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, text, func, JSON, VARCHAR
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

import json

from config import config


class ModelBase(DeclarativeBase):
    pass


class BaseConfig:
    what: str
    description: str


class DatabaseConfig(ModelBase):
    __tablename__ = f"{config.db_prefix}bot_config"
    what: Mapped[str] = mapped_column(VARCHAR(length=64), primary_key=True)
    detail: Mapped[dict] = mapped_column(JSON)

    def __init__(self, sys_config: BaseConfig = None, **kw):
        super().__init__(**kw)
        self.detail = sys_config.__dict__
        self.what = str(self.detail["what"])
