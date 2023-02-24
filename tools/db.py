import os
from datetime import datetime, timezone

import aiosqlite
from aiosqlite.core import Connection
from models import USER_ROLE_CHOICES, User
from settings.config import ADMIN_USERNAME, DB_NAME
from telegram import Update


async def check_or_create_db() -> None:
    if not os.path.exists(DB_NAME):
        print(DB_NAME + ' not found!')
        async with aiosqlite.connect(DB_NAME) as db:
            await db.executescript("""
CREATE TABLE "user_role" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(10) NOT NULL UNIQUE);
CREATE TABLE "user" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "username" varchar(255) NOT NULL UNIQUE,
    "first_name" varchar(255) NOT NULL,
    "telegram_id" integer NOT NULL UNIQUE,
    "language_code" varchar(2) NOT NULL,
    "time_added" datetime NOT NULL,
    "role_id" bigint NOT NULL REFERENCES "user_role" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE "user_message" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" varchar(10) NOT NULL UNIQUE, "message_id" integer NOT NULL,
    "time_added" datetime NOT NULL,
    "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX "user_role_id_c3a87a3d" ON "user" ("role_id");
CREATE INDEX "user_message_user_id_8a912feb" ON "user_message" ("user_id");
INSERT INTO `user_role` (`id`, `name`) VALUES
    (1, 'admin'),
    (2, 'client'),
    (3, 'alient'),
    (4, 'blocked');""")
            await db.commit()


async def get_user_by_username(username: str, db: Connection | None = None) -> User | None:
    if db:
        async with db.execute(f"SELECT * FROM user WHERE username='{username}';") as cursor:
            user = await cursor.fetchone()
    else:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(f"SELECT * FROM user WHERE username='{username}';") as cursor:
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
            print('role_id', role_id)
            await db.execute(f"""
INSERT INTO user (username, first_name, telegram_id, language_code, role_id, time_added) VALUES
('{tuser.username}', '{tuser.first_name}', {tuser.id}, '{tuser.language_code}', {role_id}, '{time_added}');""")
            await db.commit()
        user = await get_user_by_username(tuser.username, db)
        return user


async def set_user_role(update: Update, username: str, role_name='client') -> None:
    user = await get_or_create_user(update)
    # TODO: allow only for admin: if user and user.is_admin
    if user:
        async with aiosqlite.connect(DB_NAME) as db:
            role_id = USER_ROLE_CHOICES[role_name]
            await db.execute(f"UPDATE user SET role_id={role_id} WHERE username='{username}';")
            await db.commit()


async def save_message(update: Update):
    pass
