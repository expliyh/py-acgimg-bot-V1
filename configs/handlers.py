import asyncio
import json
import logging
import random
import re

import telegram.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .generate_inline_keyboard import *
from .backblaze_config import BackblazeConfig
from chat_stats import chat_status, CONFIG_IMAGE_BED_SET
from .image_bed_edit_message_handler import image_bed_edit_message_handler

import database as db_class
from database import database


async def config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf_message = """
    欢迎使用 py-acgimg-bot 设置菜单，请在下方选择您需要的设置项。
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=conf_message,
        reply_markup=InlineKeyboardMarkup(config_main_menu_keyboard())
    )


async def config_image_bed_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.callback_query.data.split(':')
    print(command)
    if len(command) == 2:
        return await config_image_bed(update, context)
    match command[2]:
        case "set":
            return await config_image_bed_set(update, context)
        case "change":
            return await config_image_bed_change(update, context)
        case "edit":
            return await config_image_bed_edit(update, context)


async def config_image_bed_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    type = (await database.get_config('img_bed'))['description']
    command = update.callback_query.data.split(':')
    match type:
        case 'BackBlaze':
            attachment = {
                'target': command[3],
                'type': 'BackBlaze',
                'panel_id': update.callback_query.message.id
            }
            chat_status.set_stats(
                chat_id=update.effective_chat.id,
                stats=CONFIG_IMAGE_BED_SET
            )
            chat_status.set_attachment(
                chat_id=update.effective_chat.id,
                attachment=attachment
            )
    message = f"下面，请将 {command[3]} 发送给我"
    await context.bot.edit_message_text(
        text=message,
        reply_markup=None,
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id
    )
    return


async def config_image_bed_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.callback_query.data.split(':')
    match command[3]:
        case "backblaze":
            bb_conf = BackblazeConfig()
            await database.set_config("img_bed", bb_conf.__dict__)
        case _:
            return
    await context.bot.edit_message_text(
        text="修改完成，点击下面的按钮继续配置",
        reply_markup=InlineKeyboardMarkup(config_main_menu_keyboard()),
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id
    )
    return


async def config_image_bed_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await database.delete_config("img_bed")
    from image_bed import image_bed
    image_bed.init_image_bed()
    await context.bot.edit_message_text(
        text="图床自动化已取消",
        reply_markup=None,
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id
    )
    return


async def config_image_bed_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "请选择您希望使用的图床，请注意：如果不需要修改应点击 返回。否则配置将被清空"
    await context.bot.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(config_img_bed_change_keyboard()),
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id
    )


async def config_image_bed(update: Update, context: ContextTypes.DEFAULT_TYPE, panel_id: int = None):
    bed_conf_dict = await database.get_config("img_bed")
    if bed_conf_dict is None or len(bed_conf_dict) == 0:
        message = "您当前未使用图床自动化，要设置图床自动化请点击下面的 更换图床"
        await context.bot.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(config_img_bed_none_edit_keyboard()),
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id
        )
        return
    img_bed_message = f"您当前使用的图床为 {bed_conf_dict['description']}"
    reply_markup = None
    match bed_conf_dict['description']:
        case "BackBlaze":
            bed_conf = BackblazeConfig()
            bed_conf.__dict__.update(bed_conf_dict)
            img_bed_message += '\n'
            img_bed_message += bed_conf.get_conf_brief()
            img_bed_message += "要修改配置，请在下方选择您要修改的项"
            reply_markup = InlineKeyboardMarkup(config_img_bed_backblaze_edit_keyboard())
    if panel_id is None:
        await context.bot.editMessageText(
            text=img_bed_message,
            reply_markup=reply_markup,
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.id
        )
    else:
        await context.bot.editMessageText(
            text=img_bed_message,
            reply_markup=reply_markup,
            chat_id=update.effective_chat.id,
            message_id=panel_id
        )
    return


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.callback_query.data.split(':')
    if command[0] != "config":
        raise Exception(f"错误，将{command[0]}回调请求转发到 config 模块")
    match command[1]:
        case 'image_bed':
            return await config_image_bed_switch(update, context)
    pass
