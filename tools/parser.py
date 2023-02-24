import re
from models import USER_ROLE_CHOICES


async def parse_setrole_message(message: str) -> tuple:
    message = message.strip()
    message = re.sub(" +", " ", message)
    message = message.replace("/setrole ", "")
    split_message = message.split()
    if len(split_message) != 2:
        return "Wrong command!", "", ""

    username, role = split_message
    if role not in USER_ROLE_CHOICES.keys():
        return "Wrong role name!", "", ""
    return "", username, role
