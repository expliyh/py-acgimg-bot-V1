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
    if await database.get_image_info_by_pixiv_id(int(pixiv_id)) is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：重复提交")
        return
    try:
        pixiv_id = int(pixiv_id)
    except ValueError as ex:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：illust_id为非数字")
        return
    illust_detail = await pixiv_api.get_illust_info_by_pixiv_id(pixiv_id)
    if illust_detail.page_count == 1:
        original_urls: list = [illust_detail.meta_single_page['original_image_url'], ]
    else:
        original_urls = list()
        for i in illust_detail.meta_pages:
            original_urls.append(i['image_urls']['original'])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="请注意：您提交的图片页数大于一，目前可能出现错误，敬请谅解。"
        )
        if len(original_urls) != illust_detail.page_count:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="错误：links长度与page_count不一致，程序退出！"
            )
            return

    global __session
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="稍后我将向您发送您提供的图片，请按顺序将图片上传到图床后将链接按顺序发送给我，如果您配置了图床自动化，稍后我会尝试自动上传"
    )
    for i in range(illust_detail.page_count):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="正在下载图片 %d" % i
        )
        parsed_url = urlparse(original_urls[i])
        suffix = os.path.splitext(original_urls[i])[-1]
        proxy_url = parsed_url.scheme + '://' + pixiv_image_proxy_host + parsed_url.path
        cnt = 0
        latest_code = -1
        cnt_max = 5
        save_path = path + "submitted_%d_%d%s" % (illust_detail.pixiv_id, i, suffix)
        if not os.path.exists(save_path):
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
            if cnt >= cnt_max:
                if os.path.exists(path):
                    os.remove(path)
                raise FailedToDownload(code)

            file = await aiofiles.open(save_path, mode="+wb")
            await file.write(file_byte)
        else:
            file = await aiofiles.open(save_path, mode="rb")
            file_byte = await file.read()
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_byte,
            filename=f"{pixiv_id}_{i}{suffix}",
            write_timeout=120, read_timeout=60
        )
        await file.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="发送完成，请按顺序将图片上传到图床后将链接按顺序发送给我"
    )

    img_bed_config = await database.get_config('img_bed')

    if img_bed_config is not None and img_bed_config['description'] is not None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"您设置了 {img_bed_config['description']} 图床自动化，正在尝试自动上传"
        )
        from image_bed import image_bed
        for i in range(illust_detail.page_count):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="正在上传图片 %d" % i
            )
            parsed_url = urlparse(original_urls[i])
            suffix = os.path.splitext(original_urls[i])[-1]
            save_path = path + "submitted_%d_%d%s" % (illust_detail.pixiv_id, i, suffix)
            file = await aiofiles.open(save_path, mode="rb")
            file_byte = await file.read()
            print(image_bed.__dict__)

            link = image_bed.upload_image(
                file_name=f"{pixiv_id}_{i}{suffix}",
                document=file_byte
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"链接为 {link}"
            )
            await submit_link_internal(
                update,
                context,
                pixiv_id=pixiv_id,
                sub_id=i,
                link=link
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="自动上传完成，如果过程中没有报错那么则成功"
        )
        return

    chat_status.set_stats(
        chat_id=update.effective_chat.id,
        stats=IMAGE_ADD_REQUIRE_LINK
    )
    record = IdSubmitRecord
    record.pixiv_id = pixiv_id
    record.submitted_links_count = 0
    chat_status.set_attachment(
        chat_id=update.effective_chat.id,
        attachment=record
    )
    return


class IdSubmitRecord:
    pixiv_id: int
    submitted_links_count: int


async def submit_link_internal(update: Update, context: ContextTypes.DEFAULT_TYPE, pixiv_id, sub_id, link):
    if update.effective_chat.id != int(config.developer_chat_id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="错误：只有管理员可以进行此操作")
        return
    global __session
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
            text=f"出错：无法访问您提供的链接 {link} ，请检查后重试"
        )
        return
    if pixiv_id is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="系统错误，请重新提交PixivID"
        )
        return
    illust_detail = await pixiv_api.get_illust_info_by_pixiv_id(pixiv_id)
    if sub_id == 0:
        db_image_info = ImageInfo()
        db_image_info.filenames = [str(pixiv_id) + '_0' + os.path.splitext(illust_detail.get_origin_link(0))[-1]]
        db_image_info.links = [link]
        db_image_info.page_count = illust_detail.page_count
        db_image_info.name = illust_detail.title
        db_image_info.author = illust_detail.author_name
        db_image_info.pixiv_id = pixiv_id
        db_image_info.author_id = illust_detail.author_id
        db_image_info.sap_ori = False
        db_image_info.tags = json.dumps(illust_detail.tags)
        db_image_info.caption = illust_detail.caption
        if illust_detail.page_count == 1:
            db_image_info.original_urls = [illust_detail.meta_single_page['original_image_url']]
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="请注意：您上传的图片页数大于一,为%d，目前可能出现错误，敬请谅解。" % illust_detail.page_count
            )
            original_urls = list()
            for i in illust_detail.meta_pages:
                original_urls.append(i['image_urls']['original'])
            db_image_info.original_urls = original_urls
        db_image_info.raw_reply = json.dumps((await pixiv_api.get_raw(pixiv_id)))
        await database.add_image_info(db_image_info)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="提交成功：新的ID为%d" % db_image_info.image_id
        )
    else:
        filename = str(pixiv_id) + '_' + str(sub_id) + \
                   os.path.splitext(illust_detail.get_origin_link(sub_id))[-1]
        await database.add_link_and_filename_by_pixiv_id(pixiv_id, link, filename)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="已添加第%d张图片" % (sub_id + 1)
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
            text="出错：无法访问您提供的链接，请检查后重试"
        )
        return
    record: IdSubmitRecord = chat_status.get_attachment(chat_id=update.effective_chat.id)
    pixiv_id = record.pixiv_id
    if pixiv_id is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="系统错误，请重新提交PixivID"
        )
        return
    illust_detail = await pixiv_api.get_illust_info_by_pixiv_id(pixiv_id)
    if record.submitted_links_count == 0:
        db_image_info = ImageInfo()
        db_image_info.filenames = [str(pixiv_id) + '_0' + os.path.splitext(illust_detail.get_origin_link(0))[-1]]
        db_image_info.links = [link]
        db_image_info.page_count = illust_detail.page_count
        db_image_info.name = illust_detail.title
        db_image_info.author = illust_detail.author_name
        db_image_info.pixiv_id = pixiv_id
        db_image_info.author_id = illust_detail.author_id
        db_image_info.sap_ori = False
        db_image_info.tags = json.dumps(illust_detail.tags)
        db_image_info.caption = illust_detail.caption
        if illust_detail.page_count == 1:
            db_image_info.original_urls = [illust_detail.meta_single_page['original_image_url']]
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="请注意：您上传的图片页数大于一,为%d，目前可能出现错误，敬请谅解。" % illust_detail.page_count
            )
            original_urls = list()
            for i in illust_detail.meta_pages:
                original_urls.append(i['image_urls']['original'])
            db_image_info.original_urls = original_urls
        db_image_info.raw_reply = json.dumps((await pixiv_api.get_raw(pixiv_id)))
        await database.add_image_info(db_image_info)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="提交成功：新的ID为%d" % db_image_info.image_id
        )
    else:
        filename = str(pixiv_id) + '_' + str(record.submitted_links_count) + \
                   os.path.splitext(illust_detail.get_origin_link(record.submitted_links_count))[-1]
        await database.add_link_and_filename_by_pixiv_id(pixiv_id, link, filename)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="已添加第%d张图片" % (record.submitted_links_count + 1)
        )
    record.submitted_links_count += 1
    if record.submitted_links_count == illust_detail.page_count:
        chat_status.clear(chat_id=update.effective_chat.id)
    else:
        chat_status.set_attachment(chat_id=update.effective_chat.id, attachment=record)
    return
