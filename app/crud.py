from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal
import uuid

from . import models, schemas

async def create_order(db: AsyncSession, order_data: schemas.OrderCreate, user_id: int):
    # Sử dụng Transaction để đảm bảo tính toàn vẹn (ACID)
    try:
        total_amount = Decimal("0.0")
        order_items_models = []
        inventory_logs = []

        # Lấy danh sách product_id cần mua
        product_ids = [item.product_id for item in order_data.items]
        
        # 1. Khóa các dòng sản phẩm trong DB (Pessimistic Locking / FOR UPDATE)
        # Chống lỗi vượt quyền bán khi nhiều người cùng đặt 1 mặt hàng (Race Condition)
        stmt = select(models.Product).where(models.Product.id.in_(product_ids)).with_for_update()
        result = await db.execute(stmt)
        products = {p.id: p for p in result.scalars().all()}

        # 2. Xử lý từng sản phẩm
        for item in order_data.items:
            product = products.get(item.product_id)
            if not product:
                raise HTTPException(status_code=404, detail=f"Sản phẩm ID {item.product_id} không tồn tại.")
            if not product.is_active:
                raise HTTPException(status_code=400, detail=f"Sản phẩm {product.name} đã ngừng kinh doanh.")
            
            # Kiểm tra tồn kho
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Sản phẩm {product.name} (SKU: {product.sku}) không đủ tồn kho. Hiện còn: {product.stock_quantity}"
                )
            
            # Trừ kho an toàn (do đã có FOR UPDATE bảo vệ)
            product.stock_quantity -= item.quantity

            # Cảnh báo tồn kho nội bộ nếu cần (có thể trigger job celery ở đây)
            # if product.stock_quantity <= product.min_stock_level:
            #     dispatch_low_stock_alert(product.id)

            # Tính toán tiền
            subtotal = product.price * item.quantity
            total_amount += subtotal

            # Tạo model OrderItem
            order_item_model = models.OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=subtotal
            )
            order_items_models.append(order_item_model)

            # Ghi log biến động kho
            inventory_log = models.InventoryLog(
                product_id=product.id,
                user_id=user_id,
                transaction_type=models.TransactionTypeEnum.OUT,
                quantity_changed=-item.quantity,
                reason="Bán hàng - Tạo đơn hàng"
            )
            inventory_logs.append(inventory_log)

        # 3. Tính toán tổng Bill
        tax = total_amount * order_data.tax_rate
        final_amount = total_amount + tax - order_data.discount

        if final_amount < 0:
            raise HTTPException(status_code=400, detail="Chiết khấu không được lớn hơn tổng tiền sau thuế.")

        # 4. Tạo Order model
        new_order = models.Order(
            customer_id=order_data.customer_id,
            user_id=user_id, # Của nhân viên tạo đơn / Admin
            status=models.OrderStatusEnum.COMPLETED,
            total_amount=total_amount,
            tax=tax,
            discount=order_data.discount,
            final_amount=final_amount,
            payment_method=order_data.payment_method,
            items=order_items_models # Cascade save
        )

        # 5. Thêm vào Session và lưu vào Database
        db.add(new_order)
        db.add_all(inventory_logs)
        
        # db.commit() sẽ tự động kết thúc block `with_for_update()` và mở khóa dòng
        await db.commit()
        await db.refresh(new_order)
        
        # 6. Load relationships để trả về Response hoàn chỉnh (tránh N+1 query)
        stmt_load = select(models.Order).options(
            selectinload(models.Order.items).selectinload(models.OrderItem.product)
        ).where(models.Order.id == new_order.id)
        res = await db.execute(stmt_load)
        return res.scalar_one()

    except HTTPException:
        # Re-raise HTTP exceptions, tự động rollback chưa được commit
        await db.rollback()
        raise
    except Exception as e:
        # Nếu có bất kỳ lỗi nào như đứt kết nối, lỗi logic database... đều phục hồi trạng thái cũ
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi tạo đơn hàng: {str(e)}")

async def get_inventory(db: AsyncSession) -> List[models.Product]:
    # Lấy danh sách tồn kho (Sản phẩm đang kinh doanh)
    stmt = select(models.Product).where(models.Product.is_active == True).order_by(models.Product.name)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_invoices(db: AsyncSession) -> List[models.Order]:
    # Lấy danh sách hóa đơn gần nhất (Kéo cả items bên trong)
    stmt = select(models.Order).options(
        selectinload(models.Order.items).selectinload(models.OrderItem.product)
    ).order_by(models.Order.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def restock_inventory(db: AsyncSession, product_id: int, quantity: int, user_id: int) -> models.Product:
    # 1. Tìm sản phẩm và khóa dòng (for update) để tránh xung đột
    stmt = select(models.Product).where(models.Product.id == product_id).with_for_update()
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Sản phẩm ID {product_id} không tồn tại.")
        
    # 2. Cộng kho
    product.stock_quantity += quantity
    
    # 3. Ghi log Nhập kho
    inventory_log = models.InventoryLog(
        product_id=product.id,
        user_id=user_id,
        transaction_type=models.TransactionTypeEnum.IN,
        quantity_changed=quantity,
        reason="Nhập thêm hàng hóa"
    )
    db.add(inventory_log)
    
    try:
        await db.commit()
        await db.refresh(product)
        return product
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu DB: {str(e)}")

async def clear_all_invoices(db: AsyncSession):
    try:
        # Xóa OrderItem trước để tránh lỗi khóa ngoại
        await db.execute(delete(models.OrderItem))
        # Sau đó xóa Order
        await db.execute(delete(models.Order))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa lịch sử hóa đơn: {str(e)}")

async def create_product(db: AsyncSession, product_in: schemas.ProductCreate) -> models.Product:
    # Lấy category ID 1 làm mặc định
    stmt = select(models.Category).order_by(models.Category.id)
    res = await db.execute(stmt)
    category = res.scalars().first()
    
    if not category:
        raise HTTPException(status_code=500, detail="Hệ thống chưa có danh mục mặc định. Vui lòng chạy lại file seed.py.")
        
    # Tạo SKU ngẫu nhiên ngắn gọn
    generated_sku = f"SP-{str(uuid.uuid4())[:5].upper()}"
    
    new_product = models.Product(
        sku=generated_sku,
        name=product_in.name,
        price=product_in.price,
        stock_quantity=product_in.stock_quantity,
        category_id=category.id,
        is_active=True
    )
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu CSDL thêm sản phẩm: {str(e)}")

async def update_product(db: AsyncSession, product_id: int, product_in: schemas.ProductUpdate) -> models.Product:
    stmt = select(models.Product).where(models.Product.id == product_id)
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Sản phẩm ID {product_id} không tồn tại.")
    
    # Cập nhật các trường có giá trị truyền vào
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
        
    try:
        await db.commit()
        await db.refresh(product)
        return product
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật sản phẩm: {str(e)}")

async def delete_product(db: AsyncSession, product_id: int) -> bool:
    stmt = select(models.Product).where(models.Product.id == product_id)
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Sản phẩm ID {product_id} không tồn tại.")
        
    # Soft delete: Đặt is_active = False
    product.is_active = False
    
    try:
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa sản phẩm: {str(e)}")
