import re
from models import USER_ROLE_CHOICES


async def parse_setrole_command(message: str) -> tuple:
    message = re.sub(r"\s+", " ", message).strip()
    if not message.startswith("/setrole "):
        return "Wrong command!", "", ""

    _, username, role = message.split(maxsplit=2)
    if role not in USER_ROLE_CHOICES:
        return "Wrong role name!", "", ""
    return "", username, role


async def parse_addbalance_command(message: str) -> tuple:
    message = re.sub(r"\s+", " ", message).strip()
    if not message.startswith("/addbalance "):
        return "Wrong command!", "", ""

    _, username, tokens = message.split(maxsplit=2)
    try:
        tokens = int(tokens)
    except Exception as err:
        return f"Wrong tokens! {err}", "", ""
    return "", username, tokens


async def parse_context_message(message: str) -> bool:
    return True if " on" in message.lower() or "contexton" in message.lower() else False
