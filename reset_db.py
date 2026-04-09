import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base


async def reset_db():
    print("Đang kết nối tới Database...")
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

    async with engine.begin() as conn:
        print("Đang xóa toàn bộ bảng cũ (Drop all tables)...")
        await conn.run_sync(Base.metadata.drop_all)

        print("Đang tạo lại các bảng mới trắng tinh (Create all tables)...")
        await conn.run_sync(Base.metadata.create_all)

    print("Khởi tạo lại cấu trúc Database thành công!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_db())
