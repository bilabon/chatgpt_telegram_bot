import logging
from settings.config import ADMIN_USERNAME, BOT_TOKEN
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)
from tools.ai import ask_chatgpt, is_chatgpt_context_on, GPT_CONTEXT
from tools.db import (check_or_create_db, get_list_users, get_or_create_user,
                      get_user_by_username, set_user_role, save_message)
from tools.parser import parse_setrole_message, parse_context_message
from tools.user import render_list_users

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
    await update.message.reply_text(f"Welcome {user.username}! Ask admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me.")


async def contex_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Here we turn on and off the context for current user. If the context is already on, then we additionally
    clear the context. Works only with gpt-3.5-turbo.
    Example:
        /contex on
        /contex off
    """
    user = await get_or_create_user(update)
    is_message_on = parse_context_message(update.message.text)
    if is_message_on:
        if is_chatgpt_context_on(user.id):
            # here we reset context for the user
            GPT_CONTEXT.pop(user.id, None)
            GPT_CONTEXT[user.id] = []
            await update.message.reply_text("Context is cleared and enabled.")
        else:
            GPT_CONTEXT[user.id] = []
            await update.message.reply_text("Context is enabled.")
    else:
        GPT_CONTEXT.pop(user.id, None)
        await update.message.reply_text("Context is disabled.")


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
    logger.info(update)
    text_question = update.message.text

    # get or create user
    user = await get_or_create_user(update)

    # save question
    await save_message(user_id=user.id, text=text_question, message_id=update.message.message_id, message_type_id=1)

    # for pinging we do not call the chat API, just emulate the pong response.
    if text_question.lower() == 'ping':
        await update.message.reply_text('pong')
        await save_message(user_id=user.id, text='pong', message_id=None, message_type_id=2)
        return

    # user validation
    if user and not (user.is_admin or user.is_client or user.username == ADMIN_USERNAME):
        await update.message.reply_text(f'Ask admin https://t.me/{ADMIN_USERNAME} to allow you to talk to me.')
        return

    # asking chatgpt
    response = ask_chatgpt(user_id=user.id, message=text_question)
    if response:
        await save_message(user_id=user.id, text=response, message_id=None, message_type_id=2)
        await update.message.reply_text(response)
    else:
        await update.message.reply_text('500 error')


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("context", context_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_users_command))
    application.add_handler(CommandHandler("setrole", setrole_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    main()
