import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models import Base, User, Category, Product, RoleEnum
from app.database import SQLALCHEMY_DATABASE_URL

async def seed_data():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Tạo sẵn một User (nhân viên)
        admin = User(username="admin", email="admin@test.com", hashed_password="1", role=RoleEnum.ADMIN, is_active=True)
        session.add(admin)
        
        # Tạo sẵn một Category
        cat = Category(name="Mặc định", description="Danh mục chung")
        session.add(cat)
        
        # Cần flush để lấy ID của Category
        await session.flush()
        
        # Mảng sản phẩm đồng bộ với Frontend
        products = [
            Product(sku='HH01', name='Nồi Inox 3 Đáy', price=250000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH02', name='Bát Sứ Ăn Cơm (Set 10)', price=120000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH03', name='Đũa Gỗ Tự Nhiên (Set 10)', price=45000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH04', name='Cốc Thủy Tinh Chịu Nhiệt', price=55000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH05', name='Bàn Chải Đánh Răng Đặc Biệt', price=35000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH06', name='Chảo Chống Dính Mạ Đá', price=280000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH07', name='Thớt Nhựa Kháng Khuẩn', price=90000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True),
            Product(sku='HH08', name='Rổ Nhựa Đa Năng', price=35000, category_id=cat.id, stock_quantity=100, min_stock_level=10, is_active=True)
        ]
        
        session.add_all(products)
        
        try:
            await session.commit()
            print("Đã nạp dữ liệu mẫu thành công!")
        except Exception as e:
            await session.rollback()
            print("Lỗi nạp dữ liệu (có thể dữ liệu đã tồn tại):", e)
            
if __name__ == "__main__":
    asyncio.run(seed_data())
