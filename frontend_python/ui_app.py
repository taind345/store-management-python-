"""
HoaPhat Store Management - NiceGUI Frontend
Giao diện thuần Python sử dụng Component của NiceGUI & Tailwind, phong cách Claude Aesthetic.
"""

from decimal import Decimal

from nicegui import ui

from app import crud, schemas
from app.database import AsyncSessionLocal


# ============================================================
# Helper: Format tiền VND
# ============================================================
def format_currency(amount) -> str:
    """Format số tiền sang định dạng VND"""
    try:
        val = float(amount)
    except (TypeError, ValueError):
        val = 0
    return f"{val:,.0f} ₫".replace(",", ".")


def setup_pages():
    """Đăng ký tất cả các trang NiceGUI"""

    @ui.page("/")
    async def main_page():
        # --- Theme Config (Claude Aesthetic: Cream/Earth Tones) ---
        ui.colors(primary="#d97757", secondary="#8b7355", accent="#e8dcca")

        # --- Inject Google Fonts & Base Overrides ---
        ui.add_head_html("""
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
            <style>
                body { font-family: 'Inter', sans-serif; }
                /* Minimal scrollbar */
                ::-webkit-scrollbar { width: 6px; height: 6px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 10px; }
                .dark ::-webkit-scrollbar-thumb { background: #4b5563; }
                
                .nicegui-content { padding: 0 !important; max-width: 100% !important; width: 100% !important; }
            </style>
        """)

        # --- State ---
        cart = []
        current_tab = {"value": "pos"}
        products_db = []
        invoices_data = []
        search_query = {"text": ""}

        # --- View Refs ---
        pos_view_ref = None
        inv_view_ref = None
        invoices_view_ref = None
        nav_buttons = []

        # ========================================
        # DATA FUNCTIONS
        # ========================================
        async def load_products_data():
            nonlocal products_db
            async with AsyncSessionLocal() as db:
                products_db = await crud.get_inventory(db)
            return products_db

        async def load_invoices_data():
            nonlocal invoices_data
            async with AsyncSessionLocal() as db:
                invoices_data = await crud.get_invoices(db)
            return invoices_data

        # ========================================
        # TAB SWITCHING
        # ========================================
        def switch_tab(tab_id):
            current_tab["value"] = tab_id

            # Active states cho Sidebar (đổi class màu nền)
            for btn in nav_buttons:
                if btn["id"] == tab_id:
                    btn["element"].classes(
                        replace="w-full justify-start py-3 px-4 rounded-xl text-[15px] font-medium transition-colors bg-orange-50/80 text-primary dark:bg-gray-800 dark:text-gray-200"
                    )
                else:
                    btn["element"].classes(
                        replace="w-full justify-start py-3 px-4 rounded-xl text-[15px] font-medium transition-colors text-gray-600 dark:text-gray-400 hover:bg-orange-50/50 dark:hover:bg-gray-800/50"
                    )

            # Toggle view visibility
            if pos_view_ref:
                pos_view_ref.classes(
                    replace=(
                        "w-full h-full p-8 gap-8 grid grid-cols-[1fr_390px]"
                        if tab_id == "pos"
                        else "hidden"
                    )
                )
            if inv_view_ref:
                inv_view_ref.classes(
                    replace=(
                        "w-full h-full p-8 flex flex-col"
                        if tab_id == "inventory"
                        else "hidden"
                    )
                )
            if invoices_view_ref:
                invoices_view_ref.classes(
                    replace=(
                        "w-full h-full p-8 flex flex-col"
                        if tab_id == "invoices"
                        else "hidden"
                    )
                )

            # Auto-refresh
            if tab_id == "inventory":
                refresh_inventory()
            elif tab_id == "invoices":
                refresh_invoices()
            elif tab_id == "pos":
                refresh_products()

        # ========================================
        # CART LOGIC
        # ========================================
        def add_to_cart(product):
            existing = next(
                (item for item in cart if item["product_id"] == product.id), None
            )
            if product.stock_quantity <= 0:
                ui.notify(f"Sản phẩm {product.name} đã hết hàng!", type="negative")
                return
            if existing:
                existing["quantity"] += 1
            else:
                cart.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "price": float(product.price),
                        "quantity": 1,
                    }
                )
            refresh_cart()
            ui.notify(f"Đã thêm {product.name} vào giỏ", type="positive")

        def update_quantity(product_id, delta):
            idx = next(
                (i for i, item in enumerate(cart) if item["product_id"] == product_id),
                -1,
            )
            if idx > -1:
                cart[idx]["quantity"] += delta
                if cart[idx]["quantity"] <= 0:
                    cart.pop(idx)
                refresh_cart()

        def clear_cart_action():
            if len(cart) > 0:
                cart.clear()
                refresh_cart()
                ui.notify("Đã xóa giỏ hàng", type="warning")

        async def checkout():
            if len(cart) == 0:
                ui.notify("Không thể thanh toán, giỏ hàng đang trống!", type="negative")
                return
            order_data = schemas.OrderCreate(
                customer_id=None,
                items=[
                    schemas.OrderItemCreate(
                        product_id=item["product_id"], quantity=item["quantity"]
                    )
                    for item in cart
                ],
                discount=Decimal("0"),
                tax_rate=Decimal("0.1"),
                payment_method="Cash",
            )
            try:
                async with AsyncSessionLocal() as db:
                    result = await crud.create_order(
                        db=db, order_data=order_data, user_id=1
                    )
                ui.notify(
                    f"🎉 Thanh toán Thành Công! Tạo Đơn Số #{result.id}",
                    type="positive",
                )
                cart.clear()
                refresh_cart()
                refresh_products()
            except Exception as e:
                ui.notify(f'Lỗi: {getattr(e, "detail", str(e))}', type="negative")

        # ========================================
        # INVENTORY ACTIONS & MODALS
        # ========================================
        async def restock_product(product_id, product_name):
            with ui.dialog() as dialog, ui.card().classes(
                "rounded-3xl p-6 bg-white dark:bg-[#252527] w-[400px] border border-gray-100 dark:border-gray-800 shadow-xl"
            ):
                ui.label(f"📦 Nhập hàng: {product_name}").classes(
                    "text-xl font-bold mb-4 dark:text-gray-100"
                )

                with ui.column().classes("w-full gap-1 mb-6"):
                    ui.label("Số lượng nhập thêm").classes(
                        "font-medium text-gray-500 dark:text-gray-400 ml-1 text-sm"
                    )
                    qty_input = (
                        ui.number(value=10, format="%.0f")
                        .props("outlined")
                        .classes("w-full")
                    )

                with ui.row().classes("justify-end gap-3 w-full"):
                    ui.button("Hủy", on_click=dialog.close).props(
                        'flat text-color="grey-6" no-caps'
                    ).classes("font-medium")

                    async def do_restock():
                        qty = int(qty_input.value or 0)
                        if qty <= 0:
                            ui.notify("Số lượng không hợp lệ!", type="negative")
                            return
                        try:
                            async with AsyncSessionLocal() as db:
                                await crud.restock_inventory(
                                    db=db,
                                    product_id=product_id,
                                    quantity=qty,
                                    user_id=1,
                                )
                            ui.notify(
                                f"Đã nhập thêm +{qty} cho {product_name}!",
                                type="positive",
                            )
                            dialog.close()
                            refresh_inventory()
                        except Exception as e:
                            ui.notify(
                                f'Lỗi: {getattr(e, "detail", str(e))}', type="negative"
                            )

                    ui.button("Xác nhận", on_click=do_restock).props(
                        "unelevated no-caps"
                    ).classes("bg-primary text-white font-semibold rounded-xl px-6")
            dialog.open()

        async def open_add_product_modal():
            with ui.dialog() as dialog, ui.card().classes(
                "rounded-3xl p-0 bg-white dark:bg-[#252527] w-[500px] border border-gray-100 dark:border-gray-800 shadow-xl"
            ):
                with ui.row().classes(
                    "w-full p-6 border-b border-gray-100 dark:border-gray-800 justify-between items-center"
                ):
                    ui.label("Thêm Mặt Hàng Mới").classes(
                        "text-xl font-bold dark:text-gray-100"
                    )
                    ui.button(icon="close", on_click=dialog.close).props(
                        "flat round dense"
                    ).classes("text-gray-400")

                with ui.column().classes(
                    "w-full p-6 gap-5 bg-[#fafafa]/50 dark:bg-transparent"
                ):
                    with ui.column().classes("w-full gap-1"):
                        ui.label("Tên Mặt Hàng").classes(
                            "font-medium text-gray-500 dark:text-gray-400 ml-1 text-sm"
                        )
                        name_input = (
                            ui.input(placeholder="Ví dụ: Nước giải khát")
                            .props("outlined")
                            .classes("w-full")
                        )
                    with ui.column().classes("w-full gap-1"):
                        ui.label("Giá Bán (VNĐ)").classes(
                            "font-medium text-gray-500 dark:text-gray-400 ml-1 text-sm"
                        )
                        price_input = (
                            ui.number(placeholder="Ví dụ: 15000")
                            .props("outlined")
                            .classes("w-full")
                        )
                    with ui.column().classes("w-full gap-1"):
                        ui.label("Số Lượng Khởi Tạo").classes(
                            "font-medium text-gray-500 dark:text-gray-400 ml-1 text-sm"
                        )
                        qty_input = (
                            ui.number(value=0, format="%.0f")
                            .props("outlined")
                            .classes("w-full")
                        )

                with ui.row().classes(
                    "w-full p-6 border-t border-gray-100 dark:border-gray-800 justify-end items-center gap-3 bg-gray-50/50 dark:bg-black/20"
                ):
                    ui.button("Hủy", on_click=dialog.close).props(
                        'flat text-color="grey-6" no-caps'
                    ).classes("font-medium")

                    async def submit_product():
                        name = name_input.value.strip() if name_input.value else ""
                        price = price_input.value
                        quantity = qty_input.value
                        if not name or price is None or quantity is None:
                            ui.notify("Vui lòng điền đầy đủ thông tin!", type="warning")
                            return
                        if float(price) <= 0:
                            ui.notify("Giá phải lớn hơn 0!", type="warning")
                            return
                        try:
                            product_in = schemas.ProductCreate(
                                name=name,
                                price=Decimal(str(price)),
                                stock_quantity=int(quantity),
                            )
                            async with AsyncSessionLocal() as db:
                                await crud.create_product(db=db, product_in=product_in)
                            ui.notify(
                                f"🎉 Đã tạo mặt hàng [{name}] thành công!",
                                type="positive",
                            )
                            dialog.close()
                            refresh_inventory()
                            refresh_products()
                        except Exception as e:
                            ui.notify(
                                f'Lỗi: {getattr(e, "detail", str(e))}', type="negative"
                            )

                    ui.button("Đăng Ký", on_click=submit_product).props(
                        "unelevated no-caps"
                    ).classes("bg-primary text-white font-semibold rounded-xl px-8")
            dialog.open()

        # ========================================
        # INVOICES ACTIONS & MODALS
        # ========================================
        async def clear_all_invoices():
            with ui.dialog() as dialog, ui.card().classes(
                "rounded-3xl p-6 bg-white dark:bg-[#252527] w-[400px] border border-gray-100 dark:border-gray-800 shadow-xl"
            ):
                ui.label("⚠️ Cảnh báo").classes("text-xl font-bold text-red-500 mb-2")
                ui.label(
                    "Bạn có chắc muốn xóa vĩnh viễn toàn bộ lịch sử hóa đơn? Hành động này không thể hoàn tác!"
                ).classes("text-gray-600 dark:text-gray-400 mb-6 leading-relaxed")
                with ui.row().classes("justify-end gap-3 w-full"):
                    ui.button("Hủy", on_click=dialog.close).props(
                        'flat text-color="grey-6" no-caps'
                    ).classes("font-medium")

                    async def do_clear():
                        try:
                            async with AsyncSessionLocal() as db:
                                await crud.clear_all_invoices(db)
                            ui.notify(
                                "🗑 Đã xóa toàn bộ lịch sử hóa đơn!", type="warning"
                            )
                            dialog.close()
                            refresh_invoices()
                        except Exception as e:
                            ui.notify(f"Lỗi: {str(e)}", type="negative")

                    ui.button("Xóa tất cả", on_click=do_clear).props(
                        "unelevated no-caps"
                    ).classes("bg-red-500 text-white font-semibold rounded-xl px-6")
            dialog.open()

        def show_invoice_details(order):
            with ui.dialog() as dialog, ui.card().classes(
                "rounded-3xl p-0 bg-white dark:bg-[#252527] w-[650px] max-w-[95vw] border border-gray-100 dark:border-gray-800 shadow-xl"
            ):
                with ui.row().classes(
                    "w-full p-6 border-b border-gray-100 dark:border-gray-800 justify-between items-center bg-gray-50/50 dark:bg-black/20"
                ):
                    ui.label(f"Chi Tiết Hóa Đơn #{order.id}").classes(
                        "text-xl font-bold dark:text-gray-100"
                    )
                    ui.button(icon="close", on_click=dialog.close).props(
                        "flat round dense"
                    ).classes("text-gray-400")

                with ui.column().classes("w-full p-6 gap-0"):
                    date_str = (
                        order.created_at.strftime("%d/%m/%Y %H:%M:%S")
                        if order.created_at
                        else ""
                    )
                    with ui.row().classes(
                        "w-full justify-between text-gray-500 dark:text-gray-400 mb-6 text-sm"
                    ):
                        ui.label(f"Ngày tạo: {date_str}")
                        ui.label(f'Thanh toán: {order.payment_method or "Tiền mặt"}')

                    with ui.column().classes(
                        "w-full rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden"
                    ):
                        # Cột header
                        with ui.row().classes(
                            "w-full bg-gray-50 dark:bg-gray-800/50 p-3 text-sm font-semibold text-gray-600 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800"
                        ):
                            ui.label("Sản phẩm").classes("flex-1")
                            ui.label("Đơn giá").classes("w-24 text-right")
                            ui.label("SL").classes("w-12 text-center")
                            ui.label("Thành tiền").classes("w-32 text-right")

                        # Data rows
                        for idx, item in enumerate(order.items):
                            p = next(
                                (p for p in products_db if p.id == item.product_id),
                                None,
                            )
                            name = p.name if p else f"SP #{item.product_id}"
                            bg = (
                                "bg-white dark:bg-[#252527]"
                                if idx % 2 == 0
                                else "bg-[#fafafa]/50 dark:bg-gray-800/20"
                            )
                            with ui.row().classes(
                                f"w-full p-3 text-sm flex-nowrap items-center {bg}"
                            ):
                                ui.label(name).classes(
                                    "flex-1 truncate dark:text-gray-200"
                                )
                                ui.label(format_currency(item.unit_price)).classes(
                                    "w-24 text-right dark:text-gray-300"
                                )
                                ui.label(str(item.quantity)).classes(
                                    "w-12 text-center font-medium dark:text-gray-300"
                                )
                                ui.label(format_currency(item.subtotal)).classes(
                                    "w-32 text-right font-semibold text-gray-800 dark:text-gray-100"
                                )

                    with ui.column().classes(
                        "w-full mt-6 pt-6 border-t-[2px] border-dashed border-gray-200 dark:border-gray-800"
                    ):
                        with ui.row().classes(
                            "w-full justify-between mb-2 text-gray-600 dark:text-gray-400 font-medium"
                        ):
                            ui.label("Tổng tiền hàng:")
                            ui.label(format_currency(order.total_amount))
                        with ui.row().classes(
                            "w-full justify-between mb-4 text-red-500 font-medium"
                        ):
                            ui.label("Giảm giá:")
                            ui.label(f"- {format_currency(order.discount)}")
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label("TỔNG CỘNG:").classes(
                                "text-lg font-bold text-gray-500 dark:text-gray-400"
                            )
                            ui.label(format_currency(order.final_amount)).classes(
                                "text-2xl font-bold text-primary"
                            )

                with ui.row().classes(
                    "w-full p-5 border-t border-gray-100 dark:border-gray-800 justify-end bg-gray-50/50 dark:bg-black/20"
                ):
                    ui.button("Đã Hiểu", on_click=dialog.close).props(
                        "unelevated no-caps"
                    ).classes("bg-primary text-white font-semibold rounded-xl px-8")
            dialog.open()

        # ========================================
        # REFRESHABLE UI SECTIONS
        # ========================================
        @ui.refreshable
        async def render_products_grid():
            await load_products_data()

            sq = (search_query.get("text") or "").strip().lower()
            filtered_products = (
                [
                    p
                    for p in products_db
                    if sq in p.name.lower() or sq in (p.sku or "").lower()
                ]
                if sq
                else products_db
            )

            if not filtered_products:
                ui.label("Không tìm thấy sản phẩm nào!").classes(
                    "p-5 text-gray-500 italic text-center w-full mt-4"
                )
                return
            for product in filtered_products:
                is_out = product.stock_quantity <= 0
                icon_name = "inventory_2"
                if hasattr(product, "sku") and product.sku:
                    if "FOO" in product.sku or "SNC" in product.sku:
                        icon_name = "fastfood"
                    elif "DRK" in product.sku:
                        icon_name = "local_cafe"

                # Product Card
                card = ui.column().classes(
                    f'w-[220px] bg-white dark:bg-[#2a2a2c] rounded-[24px] border border-[#ebe7e1] dark:border-gray-800 shadow-sm hover:shadow-md hover:border-primary/30 dark:hover:border-primary/50 hover:-translate-y-1 transition-all cursor-pointer overflow-hidden {"opacity-50 grayscale-[50%]" if is_out else ""}'
                )
                card.on("click", lambda p=product: add_to_cart(p))

                with card:
                    with ui.row().classes(
                        "h-[150px] w-full bg-[#fcfaf7] dark:bg-black/20 items-center justify-center relative"
                    ):
                        ui.icon(icon_name, size="64px").classes(
                            "text-[#e6dfd5] dark:text-gray-700"
                        )
                        if is_out:
                            ui.label("Hết hàng").classes(
                                "absolute top-3 right-3 bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider"
                            )

                    with ui.column().classes(
                        "p-5 flex-1 w-full gap-2 border-t border-gray-50 dark:border-gray-800/50"
                    ):
                        ui.label(product.name).classes(
                            "text-[15px] font-semibold text-gray-800 dark:text-gray-100 line-clamp-2 leading-snug"
                        )
                        ui.space()
                        ui.label(format_currency(product.price)).classes(
                            "text-primary font-bold text-lg"
                        )
                        stock_color = (
                            "text-green-600 dark:text-green-400"
                            if product.stock_quantity > 0
                            else "text-red-500"
                        )
                        ui.label(f"Kho còn: {product.stock_quantity}").classes(
                            f"text-xs font-semibold {stock_color} opacity-90"
                        )

        @ui.refreshable
        def render_cart_section():
            with ui.column().classes("flex-1 w-full overflow-y-auto px-6"):
                if len(cart) == 0:
                    with ui.column().classes(
                        "w-full h-full items-center justify-center opacity-40 mt-12"
                    ):
                        ui.icon("shopping_basket", size="48px").classes(
                            "text-current mb-3"
                        )
                        ui.label("Chưa chọn sản phẩm nào").classes(
                            "font-medium text-[15px]"
                        )
                else:
                    for item in cart:
                        with ui.row().classes(
                            "w-full items-center p-3 mb-3 bg-[#fcfaf7] dark:bg-[#1a1a1c] border border-[#f0ebe3] dark:border-gray-800 rounded-2xl"
                        ):
                            with ui.row().classes(
                                "w-12 h-12 rounded-xl bg-gray-200/50 dark:bg-black/30 flex items-center justify-center mr-3 shrink-0"
                            ):
                                ui.icon("receipt_long").classes(
                                    "text-gray-400 dark:text-gray-500"
                                )

                            with ui.column().classes(
                                "flex-1 gap-0.5 justify-center mr-2 w-0"
                            ):
                                ui.label(item["name"]).classes(
                                    "font-semibold text-[14px] text-gray-800 dark:text-gray-200 truncate w-full"
                                )
                                ui.label(format_currency(item["price"])).classes(
                                    "text-primary font-bold text-[13px]"
                                )

                            with ui.row().classes(
                                "items-center gap-1.5 shrink-0 bg-white dark:bg-[#252527] rounded-full px-1 py-1 shadow-sm border border-gray-100 dark:border-gray-800"
                            ):
                                ui.button(
                                    icon="remove",
                                    on_click=lambda pid=item[
                                        "product_id"
                                    ]: update_quantity(pid, -1),
                                ).props("flat dense round").classes(
                                    "w-6 h-6 min-h-0 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                                )
                                ui.label(str(item["quantity"])).classes(
                                    "font-bold text-[13px] w-5 text-center text-gray-800 dark:text-gray-200"
                                )
                                ui.button(
                                    icon="add",
                                    on_click=lambda pid=item[
                                        "product_id"
                                    ]: update_quantity(pid, 1),
                                ).props("flat dense round").classes(
                                    "w-6 h-6 min-h-0 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                                )

            subtotal = sum(item["price"] * item["quantity"] for item in cart)
            tax = subtotal * 0.1
            total = subtotal + tax

            with ui.column().classes(
                "w-full p-6 bg-white dark:bg-[#2a2a2c] border-t border-[#f0ebe3] dark:border-gray-800 shrink-0"
            ):
                with ui.row().classes(
                    "w-full justify-between items-center mb-3 text-gray-500 dark:text-gray-400 font-medium text-[15px]"
                ):
                    ui.label("Tạm tính")
                    ui.label(format_currency(subtotal))
                with ui.row().classes(
                    "w-full justify-between items-center mb-5 text-gray-500 dark:text-gray-400 font-medium text-[15px]"
                ):
                    ui.label("Thuế (10%)")
                    ui.label(format_currency(tax))
                with ui.column().classes(
                    "w-full border-t border-dashed border-gray-200 dark:border-gray-700 pt-5 mb-6"
                ):
                    with ui.row().classes("w-full justify-between items-center"):
                        ui.label("Tổng cộng").classes(
                            "text-gray-800 dark:text-gray-200 text-lg font-bold"
                        )
                        ui.label(format_currency(total)).classes(
                            "text-primary text-2xl font-bold"
                        )

                ui.button(
                    "Xác nhận thanh toán", icon="credit_card", on_click=checkout
                ).props("unelevated no-caps").classes(
                    "w-full bg-primary text-white font-bold text-[15px] rounded-2xl py-4 shadow-md shadow-primary/20 hover:-translate-y-0.5 transition-transform"
                )

        @ui.refreshable
        async def render_inventory_table():
            await load_products_data()
            with ui.column().classes(
                "w-full bg-white dark:bg-[#2a2a2c] rounded-3xl border border-[#f0ebe3] dark:border-gray-800 shadow-sm overflow-hidden flex-1"
            ):

                # Table Header
                with ui.row().classes(
                    "w-full bg-[#fcfaf7] dark:bg-black/20 p-4 border-b border-[#f0ebe3] dark:border-gray-800 font-semibold text-[14px] text-gray-600 dark:text-gray-400 no-wrap"
                ):
                    ui.label("Mã SKU").classes("w-[120px]")
                    ui.label("Tên Sản Phẩm").classes("flex-1")
                    ui.label("Giá Bán").classes("w-[140px]")
                    ui.label("Tồn Kho").classes("w-[100px]")
                    ui.label("Hành động").classes("w-[120px] text-center")

                # Table Body
                with ui.column().classes("w-full overflow-y-auto no-wrap"):
                    for item in products_db:
                        with ui.row().classes(
                            "w-full p-4 items-center border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800 text-[14px] no-wrap transition-colors"
                        ):
                            ui.label(item.sku).classes(
                                "w-[120px] font-semibold text-gray-500 dark:text-gray-400"
                            )
                            ui.label(item.name).classes(
                                "flex-1 font-medium text-gray-800 dark:text-gray-200 truncate pr-2"
                            )
                            ui.label(format_currency(item.price)).classes(
                                "w-[140px] text-gray-700 dark:text-gray-300"
                            )

                            stock_color = (
                                "text-red-500"
                                if item.stock_quantity < item.min_stock_level
                                else "text-gray-800 dark:text-gray-200"
                            )
                            ui.label(str(item.stock_quantity)).classes(
                                f"w-[100px] font-bold {stock_color}"
                            )

                            with ui.row().classes("w-[120px] justify-center"):
                                ui.button(
                                    "Nhập kho",
                                    on_click=lambda pid=item.id, pname=item.name: restock_product(
                                        pid, pname
                                    ),
                                ).props("flat outline dense no-caps").classes(
                                    "text-xs font-semibold px-3 py-1 rounded-lg text-primary border border-primary/30 hover:bg-primary/10"
                                )

        @ui.refreshable
        async def render_invoices_table():
            await load_invoices_data()
            with ui.column().classes(
                "w-full bg-white dark:bg-[#2a2a2c] rounded-3xl border border-[#f0ebe3] dark:border-gray-800 shadow-sm overflow-hidden flex-1"
            ):
                # Table Header
                with ui.row().classes(
                    "w-full bg-[#fcfaf7] dark:bg-black/20 p-4 border-b border-[#f0ebe3] dark:border-gray-800 font-semibold text-[14px] text-gray-600 dark:text-gray-400 no-wrap"
                ):
                    ui.label("Mã HĐ").classes("w-[100px]")
                    ui.label("Thời Gian").classes("w-[200px]")
                    ui.label("Sản Phẩm").classes("flex-1")
                    ui.label("Tổng Tiền").classes("w-[150px]")
                    ui.label("Trạng Thái").classes("w-[120px] text-center")

                # Table Body
                with ui.column().classes("w-full overflow-y-auto no-wrap"):
                    if not invoices_data:
                        ui.label("Chưa có hóa đơn nào").classes(
                            "w-full text-center p-12 text-gray-400 font-medium"
                        )
                    else:
                        for order in invoices_data:
                            date_str = (
                                order.created_at.strftime("%d/%m/%Y %H:%M:%S")
                                if order.created_at
                                else ""
                            )
                            row = ui.row().classes(
                                "w-full p-4 items-center border-b border-gray-50 dark:border-gray-800/50 text-[14px] no-wrap hover:bg-orange-50/50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                            )
                            row.on("click", lambda o=order: show_invoice_details(o))

                            with row:
                                ui.label(f"#{order.id}").classes(
                                    "w-[100px] font-bold text-gray-500 dark:text-gray-400"
                                )
                                ui.label(date_str).classes(
                                    "w-[200px] text-gray-600 dark:text-gray-400"
                                )
                                ui.label(f"... {len(order.items)} mặt hàng").classes(
                                    "flex-1 font-medium text-gray-800 dark:text-gray-200 pr-2 truncate"
                                )
                                ui.label(format_currency(order.final_amount)).classes(
                                    "w-[150px] font-bold text-primary"
                                )

                                with ui.row().classes("w-[120px] justify-center"):
                                    ui.label("Thành Công").classes(
                                        "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-3 py-1 rounded-full text-xs font-bold tracking-wide"
                                    )

        # Helper refreshes
        def refresh_products():
            render_products_grid.refresh()

        def refresh_cart():
            render_cart_section.refresh()

        def refresh_inventory():
            render_inventory_table.refresh()

        def refresh_invoices():
            render_invoices_table.refresh()

        # ========================================
        # MAIN LAYOUT OVERHAUL
        # ========================================
        with ui.row().classes(
            "w-full h-screen no-wrap bg-[#fcfbf9] dark:bg-[#1a1a1c] text-gray-800 dark:text-gray-200 font-sans"
        ):

            # ---- SIDEBAR (Fixed Left) ----
            with ui.column().classes(
                "w-[280px] h-full bg-white dark:bg-[#252527] border-r border-[#f0ebe3] dark:border-gray-800 shrink-0 z-10 shadow-[2px_0_10px_rgba(0,0,0,0.02)]"
            ):
                # Header Logo
                with ui.row().classes(
                    "h-[80px] w-full items-center px-6 shrink-0 border-b border-[#f0ebe3] dark:border-gray-800"
                ):
                    with ui.row().classes(
                        "w-10 h-10 rounded-xl bg-orange-50 dark:bg-gray-800 flex items-center justify-center mr-3"
                    ):
                        ui.icon("storefront", size="24px").classes("text-primary")
                    with ui.column().classes("gap-0"):
                        ui.label("HoaPhat").classes(
                            "text-[17px] font-bold tracking-tight leading-none text-gray-900 dark:text-white"
                        )
                        ui.label("Store Management").classes(
                            "text-[12px] font-medium text-gray-500 dark:text-gray-400"
                        )

                # Nav Menu
                with ui.column().classes("w-full px-4 mt-6 gap-2 flex-1"):

                    def create_nav(icon, label, tid, default_active=False):
                        btn = ui.button(icon=icon, text=label).props(
                            "flat no-caps align=left"
                        )
                        if default_active:
                            btn.classes(
                                "w-full justify-start py-3 px-4 rounded-xl text-[15px] font-medium transition-colors bg-orange-50/80 text-primary dark:bg-gray-800 dark:text-gray-200"
                            )
                        else:
                            btn.classes(
                                "w-full justify-start py-3 px-4 rounded-xl text-[15px] font-medium transition-colors text-gray-600 dark:text-gray-400 hover:bg-orange-50/50 dark:hover:bg-gray-800/50"
                            )
                        btn.on("click", lambda: switch_tab(tid))
                        nav_buttons.append({"id": tid, "element": btn})

                    create_nav("point_of_sale", "Bán Hàng (POS)", "pos", True)
                    create_nav("inventory_2", "Tồn Kho", "inventory")
                    create_nav("receipt_long", "Hóa Đơn", "invoices")

                # Footer profile / setting
                with ui.column().classes(
                    "w-full p-6 border-t border-[#f0ebe3] dark:border-gray-800 shrink-0 gap-4"
                ):
                    with ui.row().classes("items-center w-full gap-3 mt-2"):
                        ui.label("AD").classes(
                            "w-10 h-10 rounded-full bg-gray-900 dark:bg-gray-700 text-white flex items-center justify-center font-bold text-sm tracking-widest shrink-0"
                        )
                        with ui.column().classes("gap-0 flex-1 w-0"):
                            ui.label("Admin").classes(
                                "font-bold text-[14px] leading-tight text-gray-900 dark:text-white truncate w-full"
                            )
                            ui.label("admin@hoaphat.com").classes(
                                "text-[11px] font-medium text-gray-500 truncate w-full"
                            )

            # ---- MAIN CONTENT AREA ----
            with ui.column().classes("flex-1 h-full overflow-hidden relative"):

                # App Bar (Top)
                with ui.row().classes(
                    "h-[80px] w-full items-center justify-between px-8 shrink-0 bg-transparent"
                ):
                    ui.space()  # Placeholder for maybe breadcrumbs/title
                    with ui.row().classes(
                        "bg-white dark:bg-[#252527] border border-[#f0ebe3] dark:border-gray-800 rounded-full py-2 px-5 items-center w-[400px] shadow-sm"
                    ):
                        ui.icon("search").classes("text-gray-400")
                        ui.input(
                            placeholder="Tìm kiếm mặt hàng, báo cáo...",
                            on_change=lambda _: refresh_products(),
                        ).bind_value(search_query, "text").props(
                            'borderless dense clearable debounce="400"'
                        ).classes(
                            "ml-3 flex-1 text-[14px]"
                        )

                # View Container
                with ui.column().classes("flex-1 w-full overflow-hidden relative"):

                    # --- POS VIEW ---
                    pos_view_ref = ui.element("div").classes(
                        "w-full h-full p-8 gap-8 grid grid-cols-[1fr_390px]"
                    )
                    with pos_view_ref:
                        # Left List Products
                        with ui.column().classes("w-full h-full overflow-hidden"):
                            ui.label("Danh sách Sản Phẩm").classes(
                                "text-2xl font-bold mb-5 dark:text-white"
                            )

                            with ui.row().classes("gap-3 mb-6 no-wrap"):
                                for idx, cat in enumerate(["Tất cả"]):
                                    btn = (
                                        ui.button(cat)
                                        .props("unelevated no-caps")
                                        .classes(
                                            "rounded-full px-6 py-2 font-medium transition-colors border"
                                        )
                                    )
                                    if idx == 0:
                                        btn.classes(
                                            "bg-gray-900 dark:bg-gray-200 text-white dark:text-gray-900 border-transparent"
                                        )
                                    else:
                                        btn.classes(
                                            "bg-white dark:bg-transparent text-gray-600 dark:text-gray-400 border-[#f0ebe3] dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                                        )

                            with ui.row().classes(
                                "w-full flex-1 overflow-y-auto content-start gap-[20px] pb-12 flex-wrap min-h-0"
                            ):
                                render_products_grid()

                        # Right Cart Sidebar
                        with ui.column().classes(
                            "w-full h-full bg-white dark:bg-[#2a2a2c] rounded-3xl border border-[#f0ebe3] dark:border-gray-800 shadow-sm flex-col overflow-hidden"
                        ):
                            with ui.row().classes(
                                "w-full p-6 items-center justify-between border-b border-[#f0ebe3] dark:border-gray-800 shrink-0"
                            ):
                                ui.label("Giỏ hàng hiện tại").classes(
                                    "text-[18px] font-bold dark:text-white"
                                )
                                ui.button(
                                    icon="delete_outline", on_click=clear_cart_action
                                ).props("flat round dense").classes(
                                    "text-gray-400 hover:text-red-500 transition-colors bg-gray-50 hover:bg-red-50 dark:bg-gray-800 dark:hover:bg-red-900/30"
                                )

                            render_cart_section()

                    # --- INVENTORY VIEW ---
                    inv_view_ref = ui.column().classes(
                        "w-full h-full p-8 flex flex-col hidden"
                    )
                    with inv_view_ref:
                        with ui.row().classes(
                            "w-full justify-between items-center mb-6 shrink-0"
                        ):
                            ui.label("Quản lý Tồn Kho").classes(
                                "text-3xl font-bold dark:text-white"
                            )
                            with ui.row().classes("gap-3"):
                                btn_add = (
                                    ui.button(
                                        "Thêm Mới",
                                        icon="add",
                                        on_click=open_add_product_modal,
                                    )
                                    .props("unelevated no-caps")
                                    .classes(
                                        "bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 font-semibold rounded-xl px-5 py-2.5 shadow-sm"
                                    )
                                )
                                btn_ref = (
                                    ui.button(
                                        "Làm Mới",
                                        icon="refresh",
                                        on_click=lambda: (
                                            refresh_inventory(),
                                            ui.notify("Đã làm mới!", type="info"),
                                        ),
                                    )
                                    .props("outline no-caps")
                                    .classes(
                                        "bg-white dark:bg-transparent border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-xl px-5 py-2.5"
                                    )
                                )

                        render_inventory_table()

                    # --- INVOICES VIEW ---
                    invoices_view_ref = ui.column().classes(
                        "w-full h-full p-8 flex flex-col hidden"
                    )
                    with invoices_view_ref:
                        with ui.row().classes(
                            "w-full justify-between items-center mb-6 shrink-0"
                        ):
                            ui.label("Lịch sử Hóa Đơn").classes(
                                "text-3xl font-bold dark:text-white"
                            )
                            with ui.row().classes("gap-3"):
                                btn_clr = (
                                    ui.button(
                                        "Xóa Tất Cả",
                                        icon="delete_sweep",
                                        on_click=clear_all_invoices,
                                    )
                                    .props("outline no-caps")
                                    .classes(
                                        "border border-red-200 text-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-900/50 font-semibold rounded-xl px-4 py-2.5"
                                    )
                                )
                                btn_ref2 = (
                                    ui.button(
                                        "Làm Mới",
                                        icon="refresh",
                                        on_click=lambda: (
                                            refresh_invoices(),
                                            ui.notify("Đã làm mới!", type="info"),
                                        ),
                                    )
                                    .props("unelevated no-caps")
                                    .classes(
                                        "bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 font-semibold rounded-xl px-5 py-2.5 shadow-sm"
                                    )
                                )

                        render_invoices_table()

        # Khởi chạy ban đầu để load dữ liệu sản phẩm
        ui.timer(0.1, lambda: switch_tab("pos"), once=True)
