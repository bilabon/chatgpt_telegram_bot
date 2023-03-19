import aiosqlite
import logging
import os
from fixtures.initial import CREATE_TABLES_SQL
from settings.config import DB_NAME

logger = logging.getLogger("debug")


def get_db() -> aiosqlite.Connection:
    return aiosqlite.connect(DB_NAME)


async def check_or_create_db() -> None:
    if not os.path.exists(DB_NAME):
        logger.info(f"{DB_NAME} not found!")
        async with get_db() as conn:
            await conn.executescript(CREATE_TABLES_SQL)
            await conn.commit()
