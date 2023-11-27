import asyncio
import json
import logging
import random
import re

import telegram.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db_class
from database import *
import images

from .generate_inline_keyboard import *


async def check_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    pending = await database.get_current_message_by_chat_id(update.effective_chat.id)
    if pending is not None and pending.pending:
        message = "获取图片失败：您有正在进行的原图请求。\n\n" \
                  "为节约服务器开销，您在请求原图时不可以获取新的图片\n" \
                  "此消息和您的指令将在 10 秒后自动删除。"
        msg1 = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_to_message_id=update.message.id
        )
        await asyncio.sleep(10)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg1.message_id)
        return True
    else:
        return False


async def edit_last(update: Update, context: ContextTypes.DEFAULT_TYPE):  # 修改上一条消息（操作已过期）
    current_message = await database.get_current_message_by_chat_id(update.effective_chat.id)
    if current_message is None or current_message.downloaded:
        return
    try:
        edit_task = asyncio.create_task(context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=current_message.message_id,
            reply_markup=None
        ))
        await asyncio.gather(edit_task)
    except telegram.error.TelegramError as ex:
        logging.warning(ex)


async def setu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_msg = None
    try:
        if await check_pending(update, context):
            return
        last_task = asyncio.create_task(edit_last(update, context))
        info_task = asyncio.create_task(
            context.bot.send_message(chat_id=update.effective_chat.id, text='图片发送中，请稍等……'))
        _, new_msg = await asyncio.gather(last_task, info_task)
        if isinstance(new_msg, BaseException):
            raise new_msg
        logging.info(msg="New image request: %s" % update.message)
        setu_id = random.randint(1, await database.get_max_image_id())
        cmd = context.args
        if len(cmd) > 0:
            setu_id = cmd[0]
        image_info = await database.get_image_info_by_id(setu_id)
        sub_id = random.randint(0, image_info.page_count - 1)
        if len(cmd) > 1:
            sub_id = cmd[1]
        new_current_message = CurrentMessage(
            chat_id=update.effective_chat.id,
            message_id=update.message.id,
            image_id=setu_id
        )
        queue_update_task = asyncio.create_task(
            database.update_current_message(current_message=new_current_message)
        )
        image_task = asyncio.create_task(images.get_image(setu_id, sub_id))
        future = asyncio.gather(image_task, queue_update_task)
        logging.info("Getting setu: %s" % setu_id)
        reply_markup = InlineKeyboardMarkup(get_origin_keyboard(update.effective_chat.id))
        image, _ = await future
        info_caption = "%s\n" \
                       "画师: %s\n" \
                       "图片链接: %s\n" \
                       "画师主页: %s\n" % (
                           image_info.name,
                           image_info.author,
                           image_info.get_pixiv_link(),
                           image_info.get_author_link()
                       )
        p_msg = await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=await image.read(),
            caption=info_caption,
            reply_markup=reply_markup,
            write_timeout=60,
            read_timeout=60
        )
        new_current_message.message_id = p_msg.id
        await database.update_current_message(current_message=new_current_message)
    except images.FailedToDownload as ex:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="错误：服务端错误 %s" % str(ex.code)
        )

    finally:
        if new_msg is not None and isinstance(new_msg, telegram.Message):
            await context.bot.delete_message(chat_id=new_msg.chat_id, message_id=new_msg.message_id)
