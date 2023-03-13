import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters, CallbackQueryHandler, CallbackContext)

from settings.config import ADMIN_USERNAME, BOT_TOKEN
from tools.ai import (
    ask_chatgpt, is_context_enabled, GPT_CONTEXT, disable_context_for_user, clear_context_for_user,
    enable_context_for_user, )
from tools.db import check_or_create_db
from tools.sql import (
    get_list_users, get_or_create_user,
    get_user_by_username, set_user_role, save_message)
from tools.parser import parse_setrole_message, parse_context_message
from tools.user import render_list_users
from models import USER_MODES_CONFIGS

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued.
    Example:
        /start
    """
    await check_or_create_db()
    user = await get_or_create_user(update)
    await update.message.reply_text(
        f"Welcome {user.username}! Ask admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me.")


async def context_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Here we turn on and off the context for current user. If the context is already on, then we additionally
    clear the context. Works only with gpt-3.5-turbo.
    Example:
        /contex on
        /contex off
    """
    user = await get_or_create_user(update)
    is_message_on = await parse_context_message(update.message.text)
    if is_message_on:
        if await is_context_enabled(user.id):
            # here we reset context for the user
            await clear_context_for_user(update, user.id, "Context is cleared and enabled.")
        else:
            await enable_context_for_user(update, user.id)
    else:
        await disable_context_for_user(update, user.id)


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return list of all users (only for admin).
    Example:
        /list
    """
    user = await get_or_create_user(update)
    if user and (user.is_admin or user.username == ADMIN_USERNAME):
        list_users = await get_list_users()
        response_text = await render_list_users(list_users)
        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text(f"I can say it only to admin.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Check out https://github.com/bilabon/chatgpt_telegram_bot#info ")


async def setrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A user with the role of admin can assign roles to other users.
    Example:
        /setrole username client
    """
    user = await get_or_create_user(update)
    if user and (user.is_admin or user.username == ADMIN_USERNAME):
        error, username_, role_name_ = await parse_setrole_message(update.message.text)
        if error:
            await update.message.reply_text(error)
            return
        user_ = await get_user_by_username(username_)
        if user_:
            await set_user_role(update, username_, role_name_)
            # TODO: delete, its only for debug
            updated_user_ = await get_user_by_username(username_)
            await update.message.reply_text(f"Success! {username_} now with {updated_user_.get_role_name()} role.")
        else:
            await update.message.reply_text(f"{username_} is not found!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    logger.info(f'echo() update: {update.to_json()}')
    logger.info(f'echo() GPT_CONTEXT: {GPT_CONTEXT}')
    text_question = update.message.text
    # get or create user
    user = await get_or_create_user(update)

    # save question
    await save_message(user_id=user.id, data=update)
    #    user_id=user.id, text=text_question, message_id=update.message.message_id, message_type_id=1)

    # for pinging we do not call the chat API, just emulate the pong response.
    if text_question.lower() == 'ping':
        await update.message.reply_text('pong')
        # await save_message(user_id=user.id, text='pong', message_id=None, message_type_id=2)
        return

    # user validation
    if user and not (user.is_admin or user.is_client or user.username == ADMIN_USERNAME):
        await update.message.reply_text(f'Ask admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me.')
        return

    # asking chatgpt

    text, response = await ask_chatgpt(update, user=user, message=text_question)
    # try:
    #     text, response = await ask_chatgpt(update, user=user, message=text_question)
    # except Exception as err:
    #     msg = f'500 error: {err}'
    #     await update.message.reply_text(msg)
    #     await disable_context_for_user(update, user.id)
    #     return

    if text:
        await save_message(user_id=user.id, data=response)
        await update.message.reply_text(text)
    else:
        await update.message.reply_text('500 error')
        await disable_context_for_user(update, user.id)


async def show_chat_modes_handle(update: Update, context: CallbackContext):
    user = await get_or_create_user(update)

    keyboard = []
    for mode_name, conf in USER_MODES_CONFIGS.items():
        keyboard.append([InlineKeyboardButton(conf['name'], callback_data=f"set_chat_mode|{mode_name}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select chat mode:", reply_markup=reply_markup)


async def set_chat_mode_handle(update: Update, context: CallbackContext):
    user = await get_or_create_user(update)

    query = update.callback_query
    await query.answer()
    mode_name = query.data.split("|")[1]

    await query.edit_message_text(
        f"<b>{user.get_mode_config()['name']}</b> chat mode is set",
        parse_mode=ParseMode.HTML
    )
    await disable_context_for_user(update=update, user_id=user.id, silent=True)
    await user.save_mode_name(mode_name)
    user = await get_or_create_user(update)
    await query.edit_message_text(user.get_mode_config()['welcome_message'], parse_mode=ParseMode.HTML)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("context", context_command))
    application.add_handler(CommandHandler("contexton", context_command))
    application.add_handler(CommandHandler("contextoff", context_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_users_command))
    application.add_handler(CommandHandler("setrole", setrole_command))

    application.add_handler(CommandHandler("mode", show_chat_modes_handle))
    application.add_handler(CallbackQueryHandler(set_chat_mode_handle, pattern="^set_chat_mode"))

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    main()
