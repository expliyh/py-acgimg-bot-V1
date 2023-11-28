from chat_stats import chat_status
import chat_stats
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
from image_bed import image_bed
from chat_stats import chat_status, CONFIG_IMAGE_BED_SET
from .backblaze_config import BackblazeConfig

from .generate_inline_keyboard import *


async def image_bed_edit_backblaze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attachment = chat_status.get_attachment(update.effective_chat.id)
    conf = BackblazeConfig()
    conf.__dict__.update(await database.get_config('img_bed'))
    message = update.message.text
    match attachment['target']:
        case 'app_key_id':
            conf.application_key_id = message
        case 'app_key':
            conf.application_key = message
        case 'bucket_name':
            conf.bucket_name = message
        case 'base_path':
            if message[-1] != '/':
                message += '/'
            conf.access_url_base = message
            conf.base_path = message
        case 'access_url':
            if message[-1] != '/':
                message += '/'
            conf.access_url_base = message
        case _:
            await context.bot.send_message(
                text='错误：目标不是一个配置项',
                chat_id=update.effective_chat.id
            )
            return
    await database.set_config('img_bed', conf.__dict__)
    from .handlers import config_image_bed
    image_bed.init_image_bed()
    await context.bot.send_message(
        text='配置成功',
        chat_id=update.effective_chat.id
    )
    return await config_image_bed(update, context, panel_id=int(attachment['panel_id']))


async def image_bed_edit_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attachment = chat_status.get_attachment(update.effective_chat.id)
    match attachment['type']:
        case "BackBlaze":
            return await image_bed_edit_backblaze_handler(update, context)
