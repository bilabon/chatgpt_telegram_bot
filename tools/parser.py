import re
from models import USER_ROLE_CHOICES


async def parse_setrole_message(message: str) -> tuple:
    message = re.sub(r"\s+", " ", message).strip()
    if not message.startswith("/setrole "):
        return "Wrong command!", "", ""

    _, username, role = message.split(maxsplit=2)
    if role not in USER_ROLE_CHOICES:
        return "Wrong role name!", "", ""
    return "", username, role


async def parse_context_message(message: str) -> bool:
    return True if " on" in message.lower() or "contexton" in message.lower() else False
