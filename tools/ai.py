import logging
import openai
from settings.config import AI_TOKEN, GPT_MODEL

logger = logging.getLogger(__name__)
GPT_CONTEXT = {}
GPT_CONTEXT_ROLES = {
    1: 'user',
    2: 'assistant',
}


def is_chatgpt_context_on(user_id: int) -> bool:
    """Here we are checking whether the context is on or off for a specific user. We consider the context
    to be on if the user_id key is present in the GPT_CONTEXT variable."""
    return True if user_id in GPT_CONTEXT else False


def get_or_update_chatgpt_context(message: str, user_id: int, role_id: int = 1):
    """Here we are generating a list of messages that will be sent to the chat. If the context is off,
    there will be only one message with role='user'. If the context is on, we remember the context and
    add user questions with role='user' and chat responses with role='assistant'."""
    messages = [{
        'role': GPT_CONTEXT_ROLES[role_id],
        'content': message,
    }]
    if is_chatgpt_context_on(user_id):
        messages = GPT_CONTEXT[user_id] + messages
    return messages


def ask_chatgpt(user_id: int, message: str) -> str | None:
    openai.api_key = AI_TOKEN
    response, text = None, None
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
    elif GPT_MODEL == "gpt-3.5-turbo":
        messages = get_or_update_chatgpt_context(message=message, user_id=user_id, role_id=1)
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
            get_or_update_chatgpt_context(message=text, user_id=user_id, role_id=2)
    logger.info(f'ask_chat_gpt() {GPT_MODEL} response: {response}')
    return text
