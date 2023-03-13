from telegram import Update
from telegram.ext import ContextTypes

from settings.config import ADMIN_USERNAME
from tools.db import check_or_create_db
from tools.sql import get_or_create_user


def check_user_role(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        await check_or_create_db()
        user = await get_or_create_user(update)
        if user and (user.is_admin or user.is_client or user.username == ADMIN_USERNAME):
            result = await func(update, context, user)
            return result
        elif user and user.is_alien:
            await update.message.reply_text(
                f"Welcome {user.username}! Ask admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me.")
        elif user and user.is_blocked:
            await update.message.reply_text('Sorry. You have been blocked!')

    return wrapper
