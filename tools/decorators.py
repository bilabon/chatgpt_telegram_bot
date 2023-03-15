from telegram.constants import ParseMode
from settings.config import ADMIN_USERNAME
from tools.db import check_or_create_db
from tools.sql import get_or_create_user
from tools.utils import show_user_balance


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
                result = await func(*args, **kwargs)
                return result

        # elif user and user.is_alien:
        #     reply_text = "Hi! I'm <b>ChatGPT</b> bot implemented with GPT-3.5 OpenAI API 🤖\n\n"
        #     reply_text += HELP_MESSAGE
        #     reply_text += f"\nAsk admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me!"
        #     await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

    return wrapper
