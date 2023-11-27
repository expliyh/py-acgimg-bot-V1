import html
import json
import logging
import traceback
import os
import sys

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import config
import database as db_class
from database import *
import handlers
import convert
from pixiv import PixivAPI, pixiv_api

app = ApplicationBuilder().token(config.bot_token).get_updates_read_timeout(15.0).build()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    if config.developer_chat_id is None or config.developer_chat_id == "":
        return

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096-character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message_to_developer = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"

    )
    message_to_developer_part2 = f"<pre>{html.escape(tb_string)}</pre>"

    if len(message_to_developer) + len(message_to_developer_part2) > 4090:
        part_sent = True
    else:
        message_to_developer += message_to_developer_part2
        part_sent = False

    message_to_user = (
        "处理请求时发生错误，我们已经收到关于此错误的详细报告并将尽快修复\n"
        f"<pre>{html.escape(str(tb_list[-1]))}</pre>"
    )

    # print(message_to_user)

    # Finally, send the message
    await context.bot.send_message(
        chat_id=config.developer_chat_id, text=message_to_developer, parse_mode=ParseMode.HTML
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_to_user,
        parse_mode=ParseMode.HTML
    )
    if part_sent:
        await context.bot.send_message(
            chat_id=config.developer_chat_id, text=message_to_developer_part2, parse_mode=ParseMode.HTML
        )


async def bad_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Raise an error to trigger the error handler."""
    await context.bot.wrong_method_name()  # type: ignore[attr-defined]


async def debug_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to trigger an error."""
    await update.effective_message.reply_html(
        "Use /bad_command to cause an error.\n"
        f"Your chat id is <code>{update.effective_chat.id}</code>."
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
    handlers_list = get_handlers()
    for i in handlers_list:
        app.add_handler(i)

    # Register the commands...
    app.add_handler(CommandHandler("debug", debug_start))
    app.add_handler(CommandHandler("bad_command", bad_command))
    app.add_handler(CommandHandler("info", handlers.get_info))
    app.add_handler(CommandHandler("add", handlers.submit_pixiv_id))
    app.add_handler(MessageHandler(filters.TEXT, callback=handlers.message_handler))

    # ...and the error handler
    app.add_error_handler(error_handler)

    pixapi = PixivAPI()
    pixapi.enable = True
    pixiv_api.enable = True

    app.run_polling(timeout=60, write_timeout=60)
