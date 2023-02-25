import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from tools.ai import ask_chatgpt
from tools.db import check_or_create_db, get_or_create_user, set_user_role, get_user_by_username
from tools.parser import parse_setrole_message
from settings.config import BOT_TOKEN, ADMIN_USERNAME


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await check_or_create_db()
    user = await get_or_create_user(update)
    await update.message.reply_html(f"Welcome {user.username}! Ask admin to allow you texting to me.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help command is not implemented!")


async def setrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = await get_user_by_username(update.effective_user.username)
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
    user = await get_or_create_user(update)
    if user and not (user.is_admin or user.is_client or user.username == ADMIN_USERNAME):
        await update.message.reply_text('Ask admin to allow you texting to me.')
        return
    response = ask_chatgpt(update.message.text)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text('500 error')


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setrole", setrole_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()