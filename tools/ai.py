import logging
import openai
from settings.config import AI_TOKEN, GPT_MODEL

logger = logging.getLogger(__name__)


def ask_chatgpt(message: str) -> str | None:
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
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": message}],
        )
        if all([
            response,
            response.choices,
            response.choices[0],
            response.choices[0].message,
            response.choices[0].message.content
        ]):
            text = response.choices[0].message.content
    logger.info(f'ask_chat_gpt() {GPT_MODEL} response: {response}')
    return text
