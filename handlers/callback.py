import asyncio
import json
import logging
import os.path

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
import configs
import database as db_class
from database import *
import images
from .generate_inline_keyboard import *


async def get_origin(update: Update, context: ContextTypes.DEFAULT_TYPE, query: dict):
    chat_id = update.effective_chat.id
    current_message = await database.get_current_message_by_chat_id(chat_id)
    # is_pending_snap = await database.db.is_pending(chat_id)
    await asyncio.gather(
        asyncio.create_task(database.set_pending(chat_id, True))
    )
    try:
        queue_info = await database.get_current_message_by_chat_id(chat_id)
        if queue_info is not None:
            if update.callback_query.message.message_id != queue_info.message_id:
                logging.warning("ID unmatch! The call is %s while %s in database" % (
                    update.callback_query.message.message_id, queue_info.message_id))
        if queue_info is None:
            answer_task = asyncio.create_task(update.callback_query.answer(text="错误，数据库中找不到对应的请求"))
            edit_task = asyncio.create_task(context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(get_origin_fail_keyboard(
                    chat_id=chat_id,
                    reason="数据库中没有对应数据",
                    no_retry=True
                ))
            ))
            await asyncio.gather(answer_task, edit_task)
            return
        # 若图片 chat_id 不一致
        elif int(query['cid']) != chat_id:
            await update.callback_query.answer(text="获取失败：请不要获取转发的消息的原图！", show_alert=True)
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=update.message.message_id,
                reply_markup=InlineKeyboardMarkup(get_origin_fail_keyboard(
                    chat_id=chat_id,
                    reason="错误: 转发的消息",
                    no_retry=True
                ))
            )
            return
        # 若有正在进行的原图请求
        elif current_message.pending:
            logging.info("Sending alert")
            await update.callback_query.answer(text="您有正在进行的原图请求，请稍后重试。", show_alert=True)
            return
        # 获取原图

        ans_task = asyncio.create_task(update.callback_query.answer(text='获取原图中，请稍候……', show_alert=False))
        keyboard_change_task = asyncio.create_task(
            context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=getting_origin_keyboard()
                )
            )
        )
        await asyncio.gather(keyboard_change_task)
        ori_task = asyncio.create_task(images.get_origin(queue_info.image_id, queue_info.sub_id))
        ori_future = asyncio.gather(ans_task, ori_task)
        _, ori = await ori_future
        if isinstance(ori, BaseException):
            raise ori
        else:
            logging.info('正在修改键盘')
            image_info = await images.get_image_info(queue_info.image_id)
            image_name = f"{image_info.name}_{queue_info.sub_id}{os.path.splitext(str(image_info.filenames[queue_info.sub_id]))[-1]}"
            logging.info(image_name)
            send_task = asyncio.create_task(
                context.bot.send_document(chat_id=chat_id, document=await ori.read(), filename=image_name,
                                          write_timeout=120, read_timeout=60)
            )
            message_edit_task = asyncio.create_task(context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=sending_origin_keyboard()
                )
            ))
            await asyncio.gather(send_task, message_edit_task)
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=already_get_origin_keyboard()
                )
            )
    except KeyError:
        await update.callback_query.answer(text="错误：回调函数结构不正确！", show_alert=False)
    except images.FailedToDownload as ex:
        answer_task = asyncio.create_task(
            update.callback_query.answer(text="图片获取失败：%s" % str(ex.code), show_alert=True))
        edit_task = asyncio.create_task(context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=get_origin_fail_keyboard(
                    chat_id=chat_id,
                    reason="服务端错误，点击重试",
                    no_retry=False
                )
            )
        ))
        await asyncio.gather(answer_task, edit_task)

    finally:
        await database.set_pending(chat_id, False)


async def already_get_origin(update: Update):
    await update.callback_query.answer(text="请不要重复获取原图，谢谢")
    return


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_str = update.callback_query
    cmd = query_str.data.split(':')
    logging.info(query_str.data)
    logging.info(update.effective_chat.id)
    if cmd[0] == "config":
        if update.effective_chat.id != int(config.config.developer_chat_id):
            return await update.callback_query.answer(text="未知操作")
        return await configs.callback_handler(update, context)
    query = json.loads(query_str.data)
    match query['op']:
        case 'gto':  # 获取原始图片
            await get_origin(update, context, query)
        case 'agto':  # 重复获取原图
            await already_get_origin(update)
        case _:
            await update.callback_query.answer(text="未知操作")
