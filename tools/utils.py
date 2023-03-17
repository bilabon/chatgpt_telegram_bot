from telegram import Update
from telegram.constants import ParseMode
from openai.openai_object import OpenAIObject

from models import User
from settings.config import ADMIN_USERNAME


async def inform_used_tokens_on_message(update: Update, response: OpenAIObject) -> None:
    text = f"🟢 You spent on last message <b>{response.usage.total_tokens}</b> tokens."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def show_user_balance(update: Update, user: User, only_reply_if_negative_balance=False) -> str | None:
    balance_spent = await user.get_balance_spent()
    balance_credited = await user.get_balance_credited()
    balance_left = balance_credited - balance_spent
    text = "🟢 " if balance_left > 2500 else "🟡 " if balance_left > 0 else "🔴 "
    text += f"You have <b>{balance_left}</b> tokens left. You totally spent <b>{balance_spent}</b> tokens." \
            f"\n\nWrite to admin @{ADMIN_USERNAME} to top up your balance."
    if only_reply_if_negative_balance and balance_left > 0:
        # if balance_left > 0 and only_reply_if_negative_balance == True we do not return reply_text
        text = None
    return text
