import logging
import tempfile
import time

import pydub
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters, CallbackQueryHandler, CallbackContext, ApplicationBuilder,
                          AIORateLimiter)

from settings.config import ADMIN_USERNAME, BOT_TOKEN, VOICE_LIMIT_DURATION_SEC
from tools.ai import (
    ask_chatgpt, is_context_enabled, GPT_CONTEXT, GPT_LAST_MESSAGE, disable_context_for_user, clear_context_for_user,
    enable_context_for_user, transcribe_audio, )
from tools.decorators import check_user_role
from tools.help import HELP_MESSAGE, HELP_MESSAGE_ADMIN
from tools.log import setup_logger
from tools.sql import (
    get_list_users, get_or_create_user,
    get_user_by_username, set_user_role, save_message, add_balance)
from tools.parser import parse_setrole_command, parse_context_message, parse_addbalance_command
from tools.user import render_list_users
from models import USER_MODES_CONFIGS, User
from tools.utils import inform_used_tokens_on_message, show_user_balance

logger = logging.getLogger("debug")


@check_user_role
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Send a message when the command /start is issued.
    Example:
        /start
    """
    await help_command(update, context)


@check_user_role
async def context_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Here we turn on and off the context for current user. If the context is already on, then we additionally
    clear the context. Works only with gpt-3.5-turbo.
    Example:
        /contex on
        /contex off
    """
    is_message_on = await parse_context_message(update.message.text)
    if is_message_on:
        if await is_context_enabled(update, user.id):
            # here we reset context for the user
            await clear_context_for_user(update, user.id, "Context is cleared and enabled.")
        else:
            await enable_context_for_user(update, user.id)
    else:
        await disable_context_for_user(update, user.id)


@check_user_role
async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Return list of all users (only for admin).
    Example:
        /list
    """
    if user.is_admin:
        list_users = await get_list_users()
        response_text = await render_list_users(list_users)
        await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("403 Forbidden.")


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return list of all users (only for admin).
    Example:
        /addbalance username 1000
    """
    user = await get_or_create_user(update)
    if user.is_admin:
        error, username_, tokens = await parse_addbalance_command(update.message.text)
        if error:
            await update.message.reply_text(error)
            return
        user_ = await get_user_by_username(username_)
        if user_:
            await add_balance(user_.id, tokens)
            user_ = await get_user_by_username(username_)
            response_text = await render_list_users([user_])
            await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("403 Forbidden.")


@check_user_role
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Send a message when the command /help is issued."""
    reply_text = "Hi! I'm <b>ChatGPT</b> bot implemented with GPT-3.5 OpenAI API 🤖\n\n"
    reply_text += HELP_MESSAGE
    if user.is_admin:
        reply_text += HELP_MESSAGE_ADMIN
    reply_text += "\nAnd now... ask me anything!"
    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /balance is issued."""
    user = await get_or_create_user(update)
    text = await show_user_balance(update, user)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@check_user_role
async def setrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """A user with the role of admin can assign roles to other users.
    Example:
        /setrole username client
    """
    if user.is_admin or user.username == ADMIN_USERNAME:
        error, username_, role_name_ = await parse_setrole_command(update.message.text)
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
    else:
        await update.message.reply_text("403 Forbidden.")


@check_user_role
async def message_handle(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, message: str = '',
                         retry: bool = False) -> None:
    start_time = time.monotonic()
    """Echo the user message."""
    logger.info(f'echo() update: {update.to_json()}')
    logger.info(f'echo() GPT_CONTEXT: {GPT_CONTEXT}')
    logger.info(f'echo() GPT_LAST_MESSAGE: {GPT_LAST_MESSAGE}')

    logger.debug(f'+++1 message_handle {time.monotonic() - start_time}')
    text_question = message or update.message.text

    await update.message.chat.send_action(action="typing")
    logger.debug(f'+++2 message_handle {time.monotonic() - start_time}')

    # save question
    await save_message(user_id=user.id, data=update, text=text_question)
    logger.debug(f'+++3 message_handle {time.monotonic() - start_time}')

    # for pinging we do not call the chat API, just emulate the pong response.
    if text_question.lower() == 'ping':
        await update.message.reply_text('pong')
        return

    # asking chatgpt
    # TODO: remove, need only for debug
    # text, response = await ask_chatgpt(update, user=user, message=text_question)
    logger.debug(f'+++4 message_handle {time.monotonic() - start_time}')
    try:
        text, response = await ask_chatgpt(update, user=user, message=text_question, retry=retry)
    except Exception as err:
        msg = f'500 error: {err}'
        await update.message.reply_text(msg)
        await disable_context_for_user(update, user.id)
        return
    logger.debug(f'+++5 message_handle {time.monotonic() - start_time}')

    if text:
        await save_message(user_id=user.id, data=response, text=text)
        logger.debug(f'+++6 message_handle {time.monotonic() - start_time}')
        # await inform_used_tokens_on_message(update, response)
        if user.mode_id == user.get_mode_choices['code_assistant']:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        elif message:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text)
        logger.debug(f'+++7 message_handle {time.monotonic() - start_time}')
    else:
        await update.message.reply_text('500 error')
        await disable_context_for_user(update, user.id)
    logger.debug(f'+++8 message_handle {time.monotonic() - start_time}')


@check_user_role
async def retry_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    """Regenerate last bot answer."""
    if not GPT_LAST_MESSAGE.get(user.id, None):
        await update.message.reply_text('🕵️ Nothing to retry. Please write a new message.')
        return
    await update.message.chat.send_action(action="typing")
    await message_handle(update, context, user=user, retry=True)


@check_user_role
async def voice_message_handle(update: Update, context: CallbackContext, user: User):
    start_time = time.monotonic()
    await update.message.chat.send_action(action="typing")
    voice = update.message.voice
    logger.debug(f'+++1 voice_message_handle {time.monotonic() - start_time}')
    if voice.duration > VOICE_LIMIT_DURATION_SEC:
        await update.message.reply_text('👮 The message is too long, try to shorten it. Limit is 30 sec.')
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        voice_ogg_path = tmp_dir / "voice.ogg"
        logger.debug(f'+++2 voice_message_handle {time.monotonic() - start_time}')

        # download
        voice_file = await context.bot.get_file(voice.file_id)
        logger.debug(f'+++3 voice_message_handle {time.monotonic() - start_time}')
        await voice_file.download_to_drive(voice_ogg_path)
        logger.debug('+++4 voice_message_handle {time.monotonic() - start_time}')

        # convert to mp3
        voice_mp3_path = tmp_dir / "voice.mp3"
        pydub.AudioSegment.from_file(voice_ogg_path).export(voice_mp3_path, format="mp3")
        logger.debug(f'+++5 voice_message_handle {time.monotonic() - start_time}')

        # transcribe
        with open(voice_mp3_path, "rb") as f:
            transcribed_text = await transcribe_audio(f)
        logger.debug(f'+++6 voice_message_handle {time.monotonic() - start_time}')

    text = f"🎤: <i>{transcribed_text}</i>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await message_handle(update, context, user=user, message=text)


@check_user_role
async def show_chat_modes_handle(update: Update, context: CallbackContext, user: User):
    keyboard = []
    for mode_name, conf in USER_MODES_CONFIGS.items():
        keyboard.append([InlineKeyboardButton(conf['name'], callback_data=f"set_chat_mode|{mode_name}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select chat mode:", reply_markup=reply_markup)


@check_user_role
async def set_chat_mode_handle(update: Update, context: CallbackContext, user: User):
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


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/retry", "Regenerate last bot answer"),
        BotCommand("/mode", "Select chat mode"),
        BotCommand("/contexton", "Messaging with context"),
        BotCommand("/contextoff", "Messaging without context"),
        BotCommand("/balance", "Show balance"),
        BotCommand("/help", "Show help"),
    ])


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    # application = Application.builder().token(BOT_TOKEN).build()

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .post_init(post_init)
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["context", "contexton", "contextoff"], context_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_users_command))
    application.add_handler(CommandHandler("setrole", setrole_command))

    application.add_handler(CommandHandler("retry", retry_command))

    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("addbalance", addbalance_command))

    application.add_handler(CommandHandler("mode", show_chat_modes_handle))
    application.add_handler(CallbackQueryHandler(set_chat_mode_handle, pattern="^set_chat_mode"))

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handle))
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handle))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    setup_logger("debug", "logs/debug.log")
    setup_logger("timeit", "logs/timeit.log")
    setup_logger("timeit_slow", "logs/timeit_slow.log")
    main()
