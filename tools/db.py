import os
from datetime import datetime, timezone
from telegram import Update

import aiosqlite
from aiosqlite.core import Connection
from models import USER_ROLE_CHOICES, User
from settings.config import ADMIN_USERNAME, DB_NAME
from fixtures.initial import CREATE_TABLES_SQL


async def check_or_create_db() -> None:
    if not os.path.exists(DB_NAME):
        print(DB_NAME + ' not found!')
        async with aiosqlite.connect(DB_NAME) as db:
            await db.executescript(CREATE_TABLES_SQL)
            await db.commit()


async def get_user_by_username(username: str, db: Connection | None = None) -> User | None:
    _sql = f"SELECT * FROM user WHERE username='{username}';"
    if db:
        async with db.execute(_sql) as cursor:
            user = await cursor.fetchone()
    else:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(_sql) as cursor:
                user = await cursor.fetchone()
    user = User(*user) if user else None
    return user


async def get_or_create_user(update: Update) -> User:
    async with aiosqlite.connect(DB_NAME) as db:
        tuser = update.effective_user
        user = await get_user_by_username(tuser.username, db)
        if not user:
            time_added = datetime.now(timezone.utc).isoformat()
            role_id = 1 if tuser.username == ADMIN_USERNAME else 3
            await db.execute(f"""
INSERT INTO user (username, first_name, telegram_id, language_code, role_id, time_added) VALUES
('{tuser.username}', '{tuser.first_name}', {tuser.id}, '{tuser.language_code}', {role_id}, '{time_added}');""")
            await db.commit()
        user = await get_user_by_username(tuser.username, db)
        return user


async def set_user_role(update: Update, username: str, role_name='client') -> None:
    user = await get_or_create_user(update)
    if user and (user.is_admin or user.username == ADMIN_USERNAME):
        async with aiosqlite.connect(DB_NAME) as db:
            role_id = USER_ROLE_CHOICES[role_name]
            await db.execute(f"UPDATE user SET role_id={role_id} WHERE username='{username}';")
            await db.commit()


async def get_list_users(db: Connection | None = None) -> list[User] | None:
    _sql = "SELECT * FROM user ORDER BY id DESC LIMIT 2000;"
    if db:
        async with db.execute(_sql) as cursor:
            rows = await cursor.fetchall()
    else:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(_sql) as cursor:
                rows = await cursor.fetchall()
    print('users', rows)
    list_users = [User(*user) for user in rows]
    return list_users


async def save_message(update: Update):
    pass
