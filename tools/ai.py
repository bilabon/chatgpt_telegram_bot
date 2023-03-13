import logging
import openai
import json
from telegram import Update
from settings.config import AI_TOKEN, GPT_MODEL

logger = logging.getLogger(__name__)
GPT_CONTEXT = {}
GPT_CONTEXT_MAXLEN = 20
GPT_CONTEXT_ROLES = {
    1: 'user',
    2: 'assistant',
}


async def disable_context_for_user(update: Update, user_id: int, msg: str = "Context is disabled."):
    GPT_CONTEXT.pop(user_id, None)
    await update.message.reply_text(msg)


async def clear_context_for_user(update: Update, user_id: int, msg: str = "Context is cleared."):
    if user_id in GPT_CONTEXT:
        GPT_CONTEXT[user_id] = []
        await update.message.reply_text(msg)


async def enable_context_for_user(update: Update, user_id: int, msg: str = "Context is enabled."):
    GPT_CONTEXT[user_id] = []
    await update.message.reply_text(msg)


async def is_context_enabled(update: Update, user_id: int) -> bool:
    """Here we are checking whether the context is on or off for a specific user. We consider the context
    to be on if the user_id key is present in the GPT_CONTEXT variable.
    + Added a limit to the context length. If the user exceeds the context length, the context
    will be wiped and disabled, and the user will need to enable the context again with a command '/context on'."""
    user_context = GPT_CONTEXT.get(user_id)
    if user_context is not None:
        if len(user_context) <= GPT_CONTEXT_MAXLEN:
            return True
        else:
            msg = "Session access limit exceeded. Context is disabled. To enable use command: /contexton"
            await disable_context_for_user(update, user_id, msg)
    return False


async def get_or_update_context(update: Update, message: str, user_id: int, role_id: int = 1) -> list | None:
    """Here we are generating a list of messages that will be sent to the chat. If the context is off,
    there will be only one message with role='user'. If the context is on, we remember the context and
    add user questions with role='user' and chat responses with role='assistant'."""
    _is_context_enabled = await is_context_enabled(update, user_id)
    if not _is_context_enabled and role_id == 2:
        return
    messages = [{
        'role': GPT_CONTEXT_ROLES[role_id],
        'content': message,
    }]
    if _is_context_enabled:
        messages = GPT_CONTEXT[user_id] + messages
        GPT_CONTEXT[user_id] = messages
    return messages


async def _ask_chatgpt_text_davinci_003(message: str) -> str | None:
    openai.api_key = AI_TOKEN
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


async def _ask_chatgpt_gpt_35_turbo(update: Update, user_id: int, message: str) -> str | None:
    openai.api_key = AI_TOKEN
    response, text = None, None
    messages = await get_or_update_context(update, message=message, user_id=user_id, role_id=1)
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=messages,
    )
    if all([
        response,
        response.choices,
        response.choices[0],
        response.choices[0].message,
        response.choices[0].message.content
    ]):
        text = response.choices[0].message.content
        await get_or_update_context(update, message=text, user_id=user_id, role_id=2)
        logger.info(f'ask_chat_gpt() {GPT_MODEL} response: {json.dumps(response.to_dict())}')
        return text, response


async def ask_chatgpt(update: Update, user_id: int, message: str) -> str | None:
    text, response = None, None
    if GPT_MODEL == "text-davinci-003":
        text, response = await _ask_chatgpt_text_davinci_003(message)
    elif GPT_MODEL == "gpt-3.5-turbo":
        text, response = await _ask_chatgpt_gpt_35_turbo(update, user_id, message)
    return text, response
