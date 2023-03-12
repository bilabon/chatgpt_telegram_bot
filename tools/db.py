import logging
import os
from datetime import datetime, timezone

import aiosqlite
from aiosqlite.core import Connection
from telegram import Update

from fixtures.initial import CREATE_TABLES_SQL
from models import USER_ROLE_CHOICES, User
from settings.config import ADMIN_USERNAME, DB_NAME

logger = logging.getLogger(__name__)


def get_db() -> aiosqlite.Connection:
    return aiosqlite.connect(DB_NAME)


async def check_or_create_db() -> None:
    if not os.path.exists(DB_NAME):
        logger.info(f"{DB_NAME} not found!")
        async with get_db() as conn:
            await conn.executescript(CREATE_TABLES_SQL)
            await conn.commit()


async def get_user_by_username(username: str, db: Connection | None = None) -> User | None:
    _sql = "SELECT * FROM user WHERE username=?;"
    args = (username,)
    async with (db or get_db()) as conn:
        async with conn.execute(_sql, args) as cursor:
            user = await cursor.fetchone()
    return User(*user) if user else None


async def get_user_by_tid(tid: int, db: Connection | None = None) -> User | None:
    _sql = "SELECT * FROM user WHERE telegram_id=?;"
    args = (tid,)
    async with (db or get_db()) as conn:
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


async def get_list_users(db: Connection | None = None) -> list[User] | None:
    _sql = "SELECT * FROM user ORDER BY id DESC LIMIT 2000;"
    async with (db or get_db()) as conn:
        async with conn.execute(_sql) as cursor:
            rows = await cursor.fetchall()
    return [User(*user) for user in rows]


async def save_message(user_id: int, text: str, message_id: int | None = None, message_type_id: int = 1):
    """Here we save all the messages: questions and answers. message_type_id: 1 - question, 2 - answer."""
    time_added = datetime.now(timezone.utc).isoformat()
    async with get_db() as conn:
        sql = """
            INSERT INTO user_message (user_id, text, message_id, message_type_id, time_added)
            VALUES (?, ?, ?, ?, ?);"""
        args = (user_id, text.strip(), message_id, message_type_id, time_added)
        await conn.execute(sql, args)
        await conn.commit()
