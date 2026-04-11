from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import List

from . import models, schemas, crud
from .database import engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng nếu chưa có (chỉ dùng cho mục đích dev, production khuyên dùng alembic)
    # LƯU Ý: Phải tạo db ở postgres trước theo đường dẫn SQLALCHEMY_DATABASE_URL
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(title="Sales Management System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên đổi thành Domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Một dependency giả lập để lấy User ID (trong thực tế sẽ lấy và verify qua JWT token)
async def get_current_user_id() -> int:
    # Ở đây giả sử User ID số 1 đang thao tác trên hệ thống
    return 1

@app.post("/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"])
async def create_order_endpoint(
    order_in: schemas.OrderCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    **Tạo đơn hàng mới (Point of Sale / Online Order)**: 
    
    Quy trình xử lý tự động trong Transaction an toàn:
    - **Locking**: Khóa dữ liệu các sản phẩm được chọn (Pessimistic locking) để chống Race Condition khi bán.
    - **Inventory**: Kiểm tra tồn kho hợp lệ, trừ tồn kho & ghi nhận lịch sử vào `InventoryLog`.
    - **Finance**: Xử lý tính toán giá tiền `subtotal`, tính thuế VAT `tax`, áp dụng `discount` linh hoạt.
    - **Create**: Tạo hóa đơn và lưu toàn bộ xuống DB an toàn. Trả về cấu trúc JSON hóa đơn hoàn chỉnh.
    """
    return await crud.create_order(db=db, order_data=order_in, user_id=current_user_id)

@app.get("/inventory", response_model=List[schemas.ProductResponse], tags=["Inventory"])
async def get_inventory_endpoint(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách quản lý tồn kho hiện tại"""
    return await crud.get_inventory(db)

@app.post("/products", response_model=schemas.ProductResponse, status_code=201, tags=["Inventory"])
async def create_product_endpoint(
    product_in: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Thêm mặt hàng mới vào kho"""
    return await crud.create_product(db=db, product_in=product_in)

@app.get("/invoices", response_model=List[schemas.OrderResponse], tags=["Orders"])
async def get_invoices_endpoint(db: AsyncSession = Depends(get_db)):
    """Lấy lịch sử các hóa đơn đã thanh toán"""
    return await crud.get_invoices(db)

@app.delete("/invoices/clear", tags=["Orders"])
async def clear_all_invoices_endpoint(db: AsyncSession = Depends(get_db)):
    """Xóa trắng toàn bộ lịch sử hóa đơn"""
    await crud.clear_all_invoices(db)
    return {"message": "Đã xóa toàn bộ lịch sử hóa đơn."}

@app.post("/inventory/{product_id}/restock", response_model=schemas.ProductResponse, tags=["Inventory"])
async def restock_inventory_endpoint(
    product_id: int,
    restock_data: schemas.InventoryRestock,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Nhập thêm số lượng tồn kho cho mặt hàng"""
    return await crud.restock_inventory(db=db, product_id=product_id, quantity=restock_data.quantity, user_id=current_user_id)


# NOTE: Frontend hiện được serve bởi NiceGUI (xem frontend_python/ui_app.py)
# Chạy ứng dụng bằng: python run.py

