import logging
import openai
import json
from telegram import Update
from openai.openai_object import OpenAIObject
from models import User
from settings.config import AI_TOKEN, GPT_MODEL

logger = logging.getLogger("debug")

openai.api_key = AI_TOKEN

GPT_LAST_MESSAGE = {}

GPT_CONTEXT = {}
GPT_CONTEXT_MAXLEN = 20

GPT_CONTEXT_ROLE_USER = 1
GPT_CONTEXT_ROLE_ASSISTANT = 2
GPT_CONTEXT_ROLE_SYSTEM = 3
GPT_CONTEXT_ROLES = {
    GPT_CONTEXT_ROLE_USER: 'user',
    GPT_CONTEXT_ROLE_ASSISTANT: 'assistant',
    GPT_CONTEXT_ROLE_SYSTEM: 'system',
}


async def disable_context_for_user(update: Update, user_id: int, msg: str = "Context is disabled.",
                                   silent: bool = False):
    global GPT_CONTEXT
    GPT_CONTEXT.pop(user_id, None)
    if not silent:
        await update.message.reply_text(msg)


async def clear_context_for_user(update: Update, user_id: int, msg: str = "Context is cleared.", silent: bool = False):
    global GPT_CONTEXT
    if user_id in GPT_CONTEXT:
        GPT_CONTEXT[user_id] = []
        if not silent:
            await update.message.reply_text(msg)


async def enable_context_for_user(update: Update, user_id: int, msg: str = "Context is enabled.", silent: bool = False):
    global GPT_CONTEXT
    GPT_CONTEXT[user_id] = []
    if not silent:
        await update.message.reply_text(msg)


async def is_context_enabled(update: Update, user_id: int) -> bool:
    """Here we are checking whether the context is on or off for a specific user. We consider the context
    to be on if the user_id key is present in the GPT_CONTEXT variable.
    + Added a limit to the context length. If the user exceeds the context length, the context
    will be wiped and disabled, and the user will need to enable the context again with a command '/context on'."""
    global GPT_CONTEXT
    user_context = GPT_CONTEXT.get(user_id)
    if user_context is not None:
        if len(user_context) <= GPT_CONTEXT_MAXLEN:
            return True
        else:
            msg = "Session access limit exceeded. Context is disabled. To enable use command: /contexton"
            await disable_context_for_user(update, user_id, msg)
    return False


async def get_or_update_context(update: Update, message: str, user: User,
                                role_id: int = GPT_CONTEXT_ROLE_USER, retry: bool = False) -> list | None:
    """Here we are generating a list of messages that will be sent to the chat. If the context is off,
    there will be only one message with role='user'. If the context is on, we remember the context and
    add user questions with role='user' and chat responses with role='assistant'."""
    global GPT_LAST_MESSAGE
    global GPT_CONTEXT

    last_message = GPT_LAST_MESSAGE.get(user.id, [])
    if retry and last_message:
        return last_message

    _is_context_enabled = await is_context_enabled(update, user.id)
    if not _is_context_enabled and role_id == GPT_CONTEXT_ROLE_ASSISTANT:
        return

    mode_config = user.get_mode_config()

    messages = GPT_CONTEXT.get(user.id, [])
    if not messages:
        # add system message to context
        messages = [{
            'role': GPT_CONTEXT_ROLES[GPT_CONTEXT_ROLE_SYSTEM],
            'content': mode_config['system_message'],
        }]
    messages.append({
        'role': GPT_CONTEXT_ROLES[role_id],
        'content': message,
    })

    if role_id == GPT_CONTEXT_ROLE_USER:
        # save last message for /retry command
        GPT_LAST_MESSAGE[user.id] = messages

    if _is_context_enabled:
        GPT_CONTEXT[user.id] = messages
    return messages


async def _ask_chatgpt_text_davinci_003(message: str) -> tuple[str | None, OpenAIObject | None]:
    response, text, = None, None
    if GPT_MODEL == "text-davinci-003":
        response = openai.Completion.create(
            model=GPT_MODEL,
            prompt=message,
            temperature=1.0,
            max_tokens=2000,
        )
        if response and response.choices and response.choices[0] and response.choices[0].text:
            if '_split' not in response.choices[0].text:
                text = response.choices[0].text
        logger.info(f'ask_chat_gpt() {GPT_MODEL} response: {json.dumps(response.to_dict())}')
    return text, response


async def _ask_chatgpt_gpt_35_turbo(update: Update, user: User, message: str, retry: bool) -> tuple[
    str | None, OpenAIObject | None]:
    response, text = None, None
    messages = await get_or_update_context(update, message=message, user=user, role_id=GPT_CONTEXT_ROLE_USER,
                                           retry=retry)
    mode_config = user.get_mode_config()
    response = await openai.ChatCompletion.acreate(
        model=GPT_MODEL,
        messages=messages,
        temperature=mode_config['temperature'],
    )
    if all([
        response,
        response.choices,
        response.choices[0],
        response.choices[0].message,
        response.choices[0].message.content
    ]):
        text = response.choices[0].message.content
        await get_or_update_context(update, message=text, user=user, role_id=GPT_CONTEXT_ROLE_ASSISTANT)
        logger.info(
            f'ask_chat_gpt() GPT_MODEL={GPT_MODEL}, mode_config={mode_config} response: {str(json.dumps(response.to_dict()))}')
        return text, response


async def ask_chatgpt(update: Update, user: User, message: str, retry: bool = False) -> tuple[
    str | None, OpenAIObject | None]:
    text, response = None, None
    if GPT_MODEL == "text-davinci-003":
        text, response = await _ask_chatgpt_text_davinci_003(message)
    elif GPT_MODEL == "gpt-3.5-turbo":
        text, response = await _ask_chatgpt_gpt_35_turbo(update, user, message, retry)
    return text, response


async def transcribe_audio(audio_file):
    r = await openai.Audio.atranscribe("whisper-1", audio_file)
    return r["text"]
