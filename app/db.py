import aiosqlite
from app.config import config


async def init_db():
    async with aiosqlite.connect(config.db_file) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id INTEGER PRIMARY KEY,
                access_token TEXT NOT NULL
            )
            """
        )
        await db.commit()


async def set_token(user_id: int, access_token: str):
    async with aiosqlite.connect(config.db_file) as db:
        await db.execute(
            """
            INSERT INTO user_tokens (user_id, access_token) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET access_token = excluded.access_token
            """,
            (user_id, access_token),
        )
        await db.commit()


async def get_token(user_id: int) -> str | None:
    async with aiosqlite.connect(config.db_file) as db:
        async with db.execute(
            "SELECT access_token FROM user_tokens WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            return None
