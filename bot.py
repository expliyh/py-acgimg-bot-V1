import logging
import os
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

from config import config
import database as db_class
from database import *
import handlers
import convert

app = ApplicationBuilder().token(config.bot_token).get_updates_read_timeout(15.0).build()

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s-%(funcName)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(msg="Start: %s" % update.update_id)
    welcome_message = """
    Welcome to setu bot!
    send "/setu" to get a image!
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)


async def git(update: Update, context: ContextTypes.DEFAULT_TYPE):
    git_message = """
    This project is opensource on github!
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=git_message)


async def get_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = str(await database.get_max_image_id())
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def get_handlers() -> list:
    i_handlers = [
        CommandHandler('start', start),
        CommandHandler('git', git),
        CommandHandler('setu', handlers.setu),
        CommandHandler('max', get_max),
        CommandHandler('convert', convert.do_convert, has_args=True),
        CallbackQueryHandler(handlers.callback_handler)
    ]

    return i_handlers


if __name__ == '__main__':
    database.create()
    db_class.create_table()
    convert.init()
    handlers = get_handlers()
    for i in handlers:
        app.add_handler(i)

    app.run_polling(timeout=60,write_timeout=60)
