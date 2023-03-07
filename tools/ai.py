import logging
import openai
from settings.config import AI_TOKEN

logger = logging.getLogger(__name__)


def ask_chatgpt(message: str) -> str | None:
    openai.api_key = AI_TOKEN
    # uncomment to use the text-davinci-003 model.
    # response = openai.Completion.create(
    #     model="text-davinci-003", prompt=message, temperature=1.0, max_tokens=2000)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )
    logger.info(f'ask_chat_gpt response: {response}')
    if all([
        response,
        response.choices,
        response.choices[0],
        response.choices[0].message,
        response.choices[0].message.content
    ]):
        return response.choices[0].message.content
