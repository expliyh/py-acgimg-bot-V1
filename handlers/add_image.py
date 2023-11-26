import asyncio
import json
import logging
import os
import random
import re
from urllib.parse import urlparse

import aiofiles
import telegram.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db_class
from config import config
from database import *
import images
import aiohttp
from chat_stats import *
from images import FailedToDownload
from pixiv import PixivAPI, pixiv_api

path = 'tmp/'

from .generate_inline_keyboard import *

__session = aiohttp.ClientSession()

pixiv_image_proxy_host = 'i.pixiv.cat'


async def submit_pixiv_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != int(config.developer_chat_id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：只有管理员可以进行此操作")
        return
    pixiv_id = context.args[0]
    if await database.get_illust_info_by_pixiv_id(pixiv_id) is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：重复提交")
        return
    try:
        pixiv_id = int(pixiv_id)
    except ValueError as ex:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：illust_id为非数字")
        return
    illust_detail = await pixiv_api.get_illust_info_by_pixiv_id(pixiv_id)
    if illust_detail.page_count == 1:
        original_url = illust_detail.meta_single_page['original_image_url']
    else:
        original_url = illust_detail.meta_pages[0]['original_image_url']
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="请注意：您提交的图片页数大于一，目前仅支持保存第一页，敬请谅解。"
        )
    parsed_url = urlparse(original_url)
    proxy_url = parsed_url.scheme + '://' + pixiv_image_proxy_host + parsed_url.path
    global __session
    cnt = 0
    latest_code = -1
    cnt_max = 5
    while 0 <= cnt < cnt_max:
        try:
            async with __session.get(proxy_url) as response:
                code = response.status
                latest_code = code
                match code:
                    case 200:
                        cnt = -100
                        file_byte = await response.read()
                    case _:
                        cnt += 1
                response.close()
        except aiohttp.ClientError as ex:
            cnt += 1
            if cnt >= cnt_max:
                raise ex
    if latest_code != 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=("出错：无法下载图片，请检查后重试 "
                  "%d" % latest_code)
        )
        return
    save_path = path + "submitted_%d.png" % illust_detail.pixiv_id
    if cnt >= cnt_max:
        if os.path.exists(path):
            os.remove(path)
        raise FailedToDownload(code)

    file = await aiofiles.open(save_path, mode="+wb")
    await file.write(file_byte)
    await file.close()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="稍后我将向您发送您提供的图片，请将该图片上传到图床后将链接发送给我"
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=file_byte,
        filename=str(pixiv_id) + os.path.splitext(original_url)[-1],
        write_timeout=120, read_timeout=60
    )
    chat_status.set_stats(
        chat_id=update.effective_chat.id,
        stats=IMAGE_ADD_REQUIRE_LINK
    )
    chat_status.set_attachment(
        chat_id=update.effective_chat.id,
        attachment=pixiv_id
    )
    return


async def submit_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != int(config.developer_chat_id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：只有管理员可以进行此操作")
        return
    global __session
    link = update.message.text
    cnt = 0
    cnt_max = 5
    latest_code = -1
    while 0 <= cnt < cnt_max:
        try:
            async with __session.get(link) as response:
                code = response.status
                latest_code = code
                match code:
                    case 200:
                        cnt = -100
                        # file_byte = await response.read()
                    case _:
                        cnt += 1
                response.close()
        except aiohttp.ClientError:
            cnt += 1
    if latest_code != 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message="出错：无法访问您提供的链接，请检查后重试"
        )
        return
    pixiv_id = chat_status.get_attachment(chat_id=update.effective_chat.id)
    if pixiv_id is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="系统错误，请重新提交PixivID"
        )
        return
    illust_detail = await pixiv_api.get_illust_info_by_pixiv_id(pixiv_id)
    db_image_info = ImageInfo()
    db_image_info.filename = str(pixiv_id) + os.path.splitext(illust_detail.get_origin_link())[-1]
    db_image_info.link = link
    db_image_info.name = illust_detail.title
    db_image_info.author = illust_detail.author_name
    db_image_info.pixiv_id = pixiv_id
    db_image_info.author_id = illust_detail.author_id
    db_image_info.sap_ori = False
    db_image_info.tags = json.dumps(illust_detail.tags)
    db_image_info.caption = illust_detail.caption
    if illust_detail.page_count == 1:
        db_image_info.original_url = illust_detail.meta_single_page['original_image_url']
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="请注意：您上传的图片页数大于一,为%d，目前仅支持保存第一页，敬请谅解。" % illust_detail.meta_pages
        )
        db_image_info.original_url = illust_detail.meta_pages[0]['original_image_url']
    db_image_info.raw_reply = json.dumps((await pixiv_api.get_raw(pixiv_id)))
    await database.add_image_info(db_image_info)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="提交成功：新的ID为%d" % db_image_info.image_id
    )
    chat_status.clear(chat_id=update.effective_chat.id)
