import logging
import os
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

from config import config
import database
import handlers

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


def get_handlers() -> list:
    i_handlers = [
        CommandHandler('start', start),
        CommandHandler('git', git),
        CommandHandler('setu', handlers.setu),
        CallbackQueryHandler(handlers.callback_handler)
    ]

    return i_handlers


if __name__ == '__main__':
    database.db.create_pool()
    handlers = get_handlers()
    for i in handlers:
        app.add_handler(i)

    app.run_polling()
