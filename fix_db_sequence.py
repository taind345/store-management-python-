import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import SQLALCHEMY_DATABASE_URL


async def fix_seq():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text(
                    "SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));"
                )
            )
            print("ĐÃ FIX LỖI TỰ ĐỘNG TĂNG ID (SEQUENCE) THÀNH CÔNG!")
        except Exception as e:
            print("Lỗi:", e)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_seq())
