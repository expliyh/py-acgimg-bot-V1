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
from .add_image import submit_link
import images
from configs import image_bed_edit_message_handler

from .generate_inline_keyboard import *


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match chat_status.get_stats(update.effective_chat.id):
        case chat_stats.NORMAL:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="非常抱歉：聊天功能暂未发布"
            )
            return
        case chat_stats.IMAGE_ADD_REQUIRE_LINK:
            await submit_link(update, context)
            return
        case chat_stats.CONFIG_IMAGE_BED_SET:
            await image_bed_edit_message_handler(update,context)
            return

