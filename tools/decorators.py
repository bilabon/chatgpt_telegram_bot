import logging
import time

from telegram.constants import ParseMode
from tools.db import check_or_create_db
from tools.sql import get_or_create_user
from tools.utils import show_user_balance

logger = logging.getLogger("debug")
logger_timeit = logging.getLogger("timeit")
logger_timeit_slow = logging.getLogger("timeit_slow")


def check_user_role(func):
    async def wrapper(*args, **kwargs):
        update = args[0]
        await check_or_create_db()
        user = await get_or_create_user(update)
        if user:
            text = await show_user_balance(update, user, only_reply_if_negative_balance=True)
            if text:
                await update.message.reply_text(text, parse_mode=ParseMode.HTML)
                return
            if user.is_blocked:
                reply_text = "Hi! I'm <b>ChatGPT</b> bot implemented with GPT-3.5 OpenAI API 🤖\n\n"
                reply_text += "Sorry. You have been blocked!"
                await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)
            else:
                # check if message is edited
                if update.edited_message is not None:
                    text = "🥲 Unfortunately, message <b>editing</b> is not supported"
                    await update.edited_message.reply_text(text, parse_mode=ParseMode.HTML)
                    return
                kwargs['user'] = user

                # timeit
                timeit_msg = 'timeit func: %r args:[%r, %r]' % (func.__name__, args, kwargs)
                start_time = time.monotonic()
                logger_timeit.debug(f'>>>Start {start_time} {timeit_msg}')
                result = await func(*args, **kwargs)
                diff = time.monotonic() - start_time
                print('diff', diff)
                logger_timeit.debug(f'>>>End {start_time} {timeit_msg} took: {diff:.4f} sec')

                logger.debug(f'>>>End {start_time} {timeit_msg} took: {diff:.4f} sec')
                if diff > 2:
                    logger_timeit_slow.debug(f'>>>End {start_time} {timeit_msg} took: {diff:.4f} sec')
                return result

    return wrapper
