import re

from . import database_old
from .database_old import db
from database import *

import telegram.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import traceback


async def do_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = context.args[0]
    dict_info = await db.get_by_id(
        ("filename", "link", "name", "author", "pixivid", "author_id", "sap_ori", "tags", "caption", "original_url",
         "reply"), int(cmd))
    image_info_in_new_format = ImageInfo()
    image_info_in_new_format.filename = dict_info["filename"]
    image_info_in_new_format.link = dict_info["link"]
    image_info_in_new_format.name = dict_info["name"]
    image_info_in_new_format.author = dict_info["author"]
    image_info_in_new_format.pixiv_id = dict_info["pixivid"]
    image_info_in_new_format.author_id = dict_info["author_id"]
    image_info_in_new_format.sap_ori = dict_info["sap_ori"]
    image_info_in_new_format.tags = dict_info["tags"]
    image_info_in_new_format.caption = dict_info["caption"]
    image_info_in_new_format.original_url = dict_info["original_url"]
    image_info_in_new_format.raw_reply = dict_info["reply"]

    exist_info = await database.get_image_info_by_filename(image_info_in_new_format.filename)
    try:
        if exist_info is not None:
            message = "图片已存在！"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        else:
            new_id = await database.add_image_info(image_info_in_new_format)
            message = "提交成功，新的ID为%d" % new_id
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    except Exception as ex:
        message = repr(ex)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        raise ex


def init():
    db.create_pool()
