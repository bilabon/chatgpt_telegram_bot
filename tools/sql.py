import json
import logging
from datetime import datetime, timezone

from openai.openai_object import OpenAIObject
from telegram import Update

from models import USER_ROLE_CHOICES, User
from settings.config import ADMIN_USERNAME, FREE_TOKENS
from tools.db import get_db

logger = logging.getLogger("debug")


async def get_user_by_username(username: str) -> User | None:
    _sql = "SELECT * FROM user WHERE username=?;"
    args = (username,)
    async with get_db() as conn:
        async with conn.execute(_sql, args) as cursor:
            user = await cursor.fetchone()
    return User(*user) if user else None


async def get_user_by_tid(tid: int) -> User | None:
    _sql = "SELECT * FROM user WHERE telegram_id=?;"
    args = (tid,)
    async with get_db() as conn:
        async with conn.execute(_sql, args) as cursor:
            user = await cursor.fetchone()
    return User(*user) if user else None


async def get_or_create_user(update: Update) -> User:
    tuser = update.effective_user
    user = await get_user_by_tid(tuser.id)
    if not user:
        time_added = datetime.now(timezone.utc).isoformat()
        role_id = 1 if tuser.username == ADMIN_USERNAME else 3
        async with get_db() as conn:
            sql = """
                INSERT INTO user (username, first_name, telegram_id, language_code, role_id, time_added)
                VALUES (?, ?, ?, ?, ?, ?);"""
            args = (tuser.username or tuser.id, tuser.first_name or '', tuser.id,
                    tuser.language_code or '', role_id, time_added)
            await conn.execute(sql, args)
            await conn.commit()
        user = await get_user_by_tid(tuser.id)
        await add_balance(user_id=user.id, tokens=FREE_TOKENS)
    return user


async def set_user_role(update: Update, username: str, role_name: str = "client") -> None:
    user = await get_or_create_user(update)
    if user and (user.is_admin or user.username == ADMIN_USERNAME):
        role_id = USER_ROLE_CHOICES[role_name]
        async with get_db() as conn:
            sql = "UPDATE user SET role_id=? WHERE username=?;"
            args = (role_id, username)
            await conn.execute(sql, args)
            await conn.commit()


async def get_list_users() -> list[User] | None:
    _sql = "SELECT * FROM user ORDER BY id DESC LIMIT 1000;"
    async with get_db() as conn:
        async with conn.execute(_sql) as cursor:
            rows = await cursor.fetchall()
    return [User(*user) for user in rows]


async def add_balance(user_id, tokens) -> None:
    time_added = datetime.now(timezone.utc).isoformat()
    async with get_db() as conn:
        sql = """
            INSERT INTO user_balance (user_id, tokens, time_added)
            VALUES (?, ?, ?);"""
        args = (user_id, tokens, time_added)
        await conn.execute(sql, args)
        await conn.commit()


# async def save_message(user_id: int, text: str, data, message_id: int | None = None, message_type_id: int = 1):
async def save_message(user_id: int, data: Update | OpenAIObject, text: str):
    """Here we save all the messages: questions and answers. message_type_id: 1 - question, 2 - answer."""
    time_added = datetime.now(timezone.utc).isoformat()
    async with get_db() as conn:
        if type(data) is Update:
            # question
            message_id = data.message.message_id
            message_type_id = 1
            total_tokens = 0
            data = data.to_json()
        elif type(data) is OpenAIObject:
            # answer
            message_id = None
            message_type_id = 2
            total_tokens = data.usage.total_tokens
            data = json.dumps(data.to_dict())
        else:
            logger.info(f"Wrong data in save_message({user_id}, {data}).")
            return
        sql = """
            INSERT INTO user_message (user_id, text, message_id, message_type_id, time_added, total_tokens, data)
            VALUES (?, ?, ?, ?, ?, ?, ?);"""
        args = (user_id, text.strip(), message_id, message_type_id, time_added, total_tokens, data)
        await conn.execute(sql, args)
        await conn.commit()
