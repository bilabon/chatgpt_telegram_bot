import openai
from settings.config import AI_TOKEN


def ask_chatgpt(message: str) -> str | None:
    openai.api_key = AI_TOKEN
    response = openai.Completion.create(
        model="text-davinci-003", prompt=message, temperature=1.0, max_tokens=2000)
    print(f'ask_chat_gpt response: {response}')
    if response and response.choices and response.choices[0] and response.choices[0].text:
        if '_split' not in response.choices[0].text:
            return response.choices[0].text
