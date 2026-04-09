from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import OrderStatusEnum


# --- User & Schema liên quan ---
class UserBase(BaseModel):
    username: str
    email: str
    role: str


# --- Product Schemas ---
class ProductBase(BaseModel):
    sku: str
    name: str
    price: Decimal
    stock_quantity: int
    is_active: bool = True


class ProductCreate(BaseModel):
    name: str = Field(..., description="Tên mặt hàng")
    price: Decimal = Field(..., gt=0, description="Giá bán")
    stock_quantity: int = Field(default=0, ge=0, description="Số lượng tồn kho ban đầu")


class ProductResponse(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Order Item Schemas ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Số lượng phải lớn hơn 0")


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    model_config = ConfigDict(from_attributes=True)


# --- Order Schemas ---
class OrderCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[OrderItemCreate]
    discount: Decimal = Field(default=Decimal("0.0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.1"), ge=0)  # Mặc định ví dụ VAT 10%
    payment_method: str = "Cash"


class OrderResponse(BaseModel):
    id: int
    customer_id: Optional[int]
    user_id: int
    status: OrderStatusEnum
    total_amount: Decimal
    tax: Decimal
    discount: Decimal
    final_amount: Decimal
    payment_method: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


# --- Inventory Schemas ---
class InventoryRestock(BaseModel):
    quantity: int = Field(gt=0, description="Số lượng nhập thêm phải lớn hơn 0")
