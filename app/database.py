from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Thay đổi bằng chuỗi kết nối PostgreSQL thật của bạn
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:T%40i03042005@localhost:5432/sales_db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
