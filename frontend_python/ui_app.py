"""
HoaPhat Store Management - NiceGUI Frontend
Thay thế hoàn toàn HTML/CSS/JS bằng Python, giữ nguyên giao diện Material Design 3.
"""
from nicegui import ui, app
from app.database import AsyncSessionLocal
from app import crud, schemas
from decimal import Decimal
import html as html_module


def el(tag: str, text: str = '', classes: str = '', style: str = ''):
    """Helper: Tạo ui.element với text content (thay cho .text() không hỗ trợ)"""
    e = ui.element(tag)
    if classes:
        e.classes(classes)
    if style:
        e.style(style)
    if text:
        e._text = text
    return e

# ============================================================
# CSS: Inject nguyên văn style.css hiện tại + Google Fonts
# ============================================================
CUSTOM_CSS = """
:root {
    --md-primary: #6200ea;
    --md-primary-hover: #4a00b0;
    --md-background: #f8f9fa;
    --md-surface: #ffffff;
    --md-error: #b00020;
    --md-text-primary: rgba(0, 0, 0, 0.87);
    --md-text-secondary: rgba(0, 0, 0, 0.6);
    --md-divider: rgba(0, 0, 0, 0.08);
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --transition-standard: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
/* Reset & Fullscreen */
html, body { height: 100vh; width: 100vw; margin: 0; padding: 0; overflow: hidden; }
body { background-color: var(--md-background); color: var(--md-text-primary); font-family: 'Roboto', sans-serif; }
* { margin: 0; padding: 0; box-sizing: border-box; }

/* Bảo vệ Icons không bị ghi đè font */
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-smoothing: antialiased;
}

/* Ép giao diện lấp đầy toàn màn hình, xóa bỏ các giới hạn max-width của Quasar/NiceGUI */
.nicegui-content { padding: 0 !important; width: 100% !important; max-width: 100% !important; }
.q-page-container { padding: 0 !important; width: 100% !important; max-width: 100% !important; }
.q-layout { min-height: 100vh !important; width: 100% !important; }
.q-page { padding: 0 !important; min-height: 100vh !important; width: 100% !important; display: flex !important; }
.q-header, .q-footer { display: none !important; }

.app-container { display: flex; width: 100vw; height: 100vh; overflow: hidden; }

/* Sidebar */
.sidebar { width: 280px; min-width: 280px; background-color: var(--md-surface); display: flex; flex-direction: column; z-index: 10; border-right: 1px solid var(--md-divider); }
q-footer { display: none !important; }

/* Material Elevations */
.elevation-1 { box-shadow: 0px 2px 4px rgba(0,0,0,0.06), 0px 4px 6px rgba(0,0,0,0.04); }
.elevation-2 { box-shadow: 0px 4px 8px rgba(0,0,0,0.08), 0px 8px 16px rgba(0,0,0,0.06); }
.elevation-3 { box-shadow: 0px 10px 20px rgba(0,0,0,0.1), 0px 16px 32px rgba(0,0,0,0.08); }

.app-container { display: flex; height: 100vh; }

/* Sidebar */
.sidebar { width: 260px; background-color: var(--md-surface); display: flex; flex-direction: column; z-index: 10; }
.sidebar-header { height: 72px; display: flex; align-items: center; padding: 0 24px; border-bottom: 1px solid var(--md-divider); }
.logo-icon { color: var(--md-primary); font-size: 32px; margin-right: 12px; }
.sidebar-header h2 { font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }
.sidebar-nav { padding: 24px 12px; display: flex; flex-direction: column; gap: 8px; }
.nav-item {
    display: flex; align-items: center;
    padding: 14px 16px; text-decoration: none; color: var(--md-text-secondary);
    border-radius: var(--radius-md); font-weight: 500; font-size: 15px;
    transition: var(--transition-standard); cursor: pointer; border: none; background: none; width: 100%; text-align: left;
}
.nav-item:hover { background-color: rgba(98, 0, 234, 0.04); color: var(--md-primary); }
.nav-item.active { background-color: rgba(98, 0, 234, 0.1); color: var(--md-primary); }
.nav-item .material-symbols-rounded { margin-right: 16px; font-size: 22px; }

/* Main Content */
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* App Bar */
.app-bar {
    height: 72px; background-color: var(--md-surface);
    display: flex; justify-content: space-between; align-items: center;
    padding: 0 32px; z-index: 5;
}
.search-bar {
    display: flex; align-items: center; background-color: var(--md-background);
    border-radius: var(--radius-xl); padding: 10px 20px; width: 480px;
    transition: var(--transition-standard);
}
.search-bar:focus-within { background-color: #fff; box-shadow: 0 0 0 2px var(--md-primary); }
.search-bar input {
    border: none; background: transparent; margin-left: 12px;
    outline: none; width: 100%; font-size: 15px; color: var(--md-text-primary);
}
.user-profile { display: flex; align-items: center; gap: 16px; }
.avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, var(--md-primary), #8e24aa);
    color: white; display: flex; justify-content: center; align-items: center;
    font-weight: 700; font-size: 14px; cursor: pointer;
}

/* View Section */
.view-section { padding: 32px; flex: 1; overflow-y: auto; display: none; }
.view-section.active { display: block; }
.page-title { font-size: 28px; font-weight: 700; margin-bottom: 24px; color: var(--md-text-primary); }

/* POS Layout */
.pos-layout { display: flex; gap: 32px; height: 100%; }
.products-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.section-title { font-size: 22px; font-weight: 700; margin-bottom: 20px; }
.category-tabs { display: flex; gap: 12px; margin-bottom: 24px; }

.md-chip {
    padding: 8px 20px; border: 1px solid var(--md-divider);
    border-radius: 32px; background: var(--md-surface);
    color: var(--md-text-secondary); font-weight: 500; font-size: 14px;
    cursor: pointer; transition: var(--transition-standard);
}
.md-chip:hover { border-color: rgba(0,0,0,0.2); color: var(--md-text-primary); }
.md-chip.active {
    background: var(--md-primary); color: white; border-color: var(--md-primary);
    box-shadow: 0 4px 8px rgba(98, 0, 234, 0.3);
}

/* Product Grid */
.products-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 24px; overflow-y: auto; padding-bottom: 32px; align-content: start;
    padding-right: 8px; flex: 1;
}
.products-grid::-webkit-scrollbar { width: 6px; }
.products-grid::-webkit-scrollbar-thumb { background: #ccc; border-radius: 10px; }

.product-card {
    background: var(--md-surface); border-radius: var(--radius-lg);
    overflow: hidden; cursor: pointer; transition: var(--transition-standard);
    border: 1px solid transparent; display: flex; flex-direction: column; min-height: 280px;
}
.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.1);
    border-color: rgba(98, 0, 234, 0.2);
}
.product-card.out-of-stock { opacity: 0.5; }

.product-img {
    height: 160px; background-color: #f1f3f4;
    display: flex; justify-content: center; align-items: center; color: var(--md-text-secondary);
    flex-shrink: 0;
}
.product-img .material-symbols-rounded { font-size: 64px; opacity: 0.2; }

.product-info { padding: 16px; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
.product-name {
    font-size: 16px; font-weight: 500; margin-bottom: 8px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--md-text-primary);
}
.product-price { color: var(--md-primary); font-weight: 700; font-size: 18px; }

/* Cart Sidebar */
.cart-sidebar {
    width: 420px; background: var(--md-surface); border-radius: var(--radius-lg);
    display: flex; flex-direction: column; overflow: hidden; height: 100%;
}
.cart-header {
    padding: 24px; border-bottom: 1px solid var(--md-divider);
    display: flex; justify-content: space-between; align-items: center;
}
.cart-header h2 { font-size: 22px; font-weight: 700; }
.btn-icon {
    cursor: pointer; color: var(--md-text-secondary); padding: 8px; border-radius: 50%;
    transition: var(--transition-standard); background: var(--md-background);
    border: none; display: flex; align-items: center; justify-content: center;
}
.btn-icon:hover { background: #ffebee; color: var(--md-error); }

.cart-items { flex: 1; overflow-y: auto; padding: 24px; }
.empty-cart-msg { text-align: center; color: var(--md-text-secondary); margin-top: 60px; font-weight: 500; }

.cart-item {
    display: flex; align-items: center; padding: 16px;
    background: var(--md-background); border-radius: var(--radius-md); margin-bottom: 16px;
}
.item-visual { width: 56px; height: 56px; border-radius: 12px; background: #e0e0e0; display: flex; justify-content: center; align-items: center; margin-right: 16px; }
.item-details { flex: 1; }
.item-name { font-weight: 500; font-size: 15px; margin-bottom: 4px; }
.item-price { color: var(--md-primary); font-weight: 700; font-size: 14px; }

.item-actions { display: flex; align-items: center; gap: 12px; }
.qty-btn {
    width: 32px; height: 32px; border-radius: 50%; border: none; background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center;
    cursor: pointer; font-size: 18px; color: var(--md-text-primary);
}
.qty-btn:hover { background: #f1f3f4; }

.cart-summary { padding: 32px 24px; background: var(--md-surface); border-top: 1px solid var(--md-divider); }
.summary-row { display: flex; justify-content: space-between; margin-bottom: 16px; color: var(--md-text-secondary); font-size: 16px; }
.total-row { font-size: 24px; font-weight: 700; color: var(--md-text-primary); margin: 24px 0 32px; padding-top: 24px; border-top: 2px dashed var(--md-divider); }

.md-button {
    border: none; border-radius: var(--radius-lg); padding: 18px 32px;
    font-size: 16px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 12px;
    transition: var(--transition-standard); text-transform: uppercase; letter-spacing: 1px;
}
.md-button.primary { background: linear-gradient(to right, var(--md-primary), #8e24aa); color: white; box-shadow: 0 6px 12px rgba(98, 0, 234, 0.3); }
.md-button.primary:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(98, 0, 234, 0.4); }
.full-width { width: 100%; }

/* Table styles for Inventory & Invoices */
.md-table { width: 100%; border-collapse: collapse; text-align: left; }
.md-table th { padding: 16px; font-weight: 500; color: #5f6368; border-bottom: 1px solid #e0e0e0; background: #f8f9fa; }
.md-table td { padding: 16px; border-bottom: 1px solid #e0e0e0; }
.md-table tr:hover { background: rgba(98, 0, 234, 0.02); }

/* Restock/action buttons in tables */
.action-btn {
    padding: 6px 16px; font-size: 13px; background: rgba(98,0,234,0.1); color: var(--md-primary);
    border: none; border-radius: var(--radius-md); cursor: pointer; font-weight: 500;
    transition: var(--transition-standard);
}
.action-btn:hover { background: rgba(98,0,234,0.2); }

.status-chip {
    padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 500;
    display: inline-block;
}
.status-chip.success { background: #e8f5e9; color: #2e7d32; }
.status-chip.danger { background: #ffebee; color: #d32f2f; }

/* Header buttons panel */
.header-actions { display: flex; gap: 12px; }
.header-btn {
    padding: 12px 20px; border-radius: var(--radius-md); border: none; cursor: pointer;
    font-weight: 500; font-size: 14px; display: flex; align-items: center; gap: 8px;
    transition: var(--transition-standard);
}
.header-btn.primary { background: linear-gradient(to right, var(--md-primary), #8e24aa); color: white; box-shadow: 0 4px 8px rgba(98,0,234,0.3); }
.header-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 6px 12px rgba(98,0,234,0.4); }
.header-btn.secondary { background: rgba(98,0,234,0.1); color: var(--md-primary); }
.header-btn.secondary:hover { background: rgba(98,0,234,0.15); }
.header-btn.danger { background: transparent; color: #d32f2f; border: 1px solid #d32f2f; }
.header-btn.danger:hover { background: rgba(211,47,47,0.05); }

/* Modal/Dialog overrides for NiceGUI */
.q-dialog__backdrop { background: rgba(0,0,0,0.4) !important; }
.custom-dialog { border-radius: var(--radius-xl) !important; }
.custom-dialog .q-card { box-shadow: 0px 10px 20px rgba(0,0,0,0.1), 0px 16px 32px rgba(0,0,0,0.08) !important; border-radius: var(--radius-xl) !important; }

/* Form */
.form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.form-group label { font-size: 14px; font-weight: 500; color: var(--md-text-secondary); }

/* Invoice detail table */
.detail-table { width: 100%; border-collapse: collapse; }
.detail-table th { padding: 12px; border-bottom: 1px solid #eee; background: #f8f9fa; font-weight: 500; color: #5f6368; }
.detail-table td { padding: 12px; border-bottom: 1px solid #eee; }

/* Stock indicator */
.stock-indicator { font-size: 11px; margin-top: 4px; font-weight: bold; }
.stock-indicator.in-stock { color: #4caf50; }
.stock-indicator.out-of-stock { color: #e53935; }
"""

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


# ============================================================
# Main Page
# ============================================================
def setup_pages():
    """Đăng ký tất cả các trang NiceGUI"""

    @ui.page('/')
    async def main_page():
        # --- Theme Config ---
        ui.colors(primary='#6200ea', secondary='#8e24aa', accent='#9c27b0')

        # --- Inject fonts & CSS ---
        ui.add_head_html('''
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
        ''')
        ui.add_css(CUSTOM_CSS)

        # --- State ---
        cart = []
        current_tab = {'value': 'pos'}
        products_db = []
        invoices_data = []

        # --- Refs cho các view sections ---
        pos_view_ref = None
        inv_view_ref = None
        invoices_view_ref = None

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
            current_tab['value'] = tab_id
            # Toggle active class on nav items
            for btn in nav_buttons:
                if btn['id'] == tab_id:
                    btn['element'].classes(add='active')
                else:
                    btn['element'].classes(remove='active')
            # Toggle view visibility
            if pos_view_ref:
                if tab_id == 'pos':
                    pos_view_ref.style('display: block')
                else:
                    pos_view_ref.style('display: none')
            if inv_view_ref:
                if tab_id == 'inventory':
                    inv_view_ref.style('display: block')
                else:
                    inv_view_ref.style('display: none')
            if invoices_view_ref:
                if tab_id == 'invoices':
                    invoices_view_ref.style('display: block')
                else:
                    invoices_view_ref.style('display: none')
            # Auto-refresh data
            if tab_id == 'inventory':
                refresh_inventory()
            elif tab_id == 'invoices':
                refresh_invoices()
            elif tab_id == 'pos':
                refresh_products()

        # ========================================
        # CART LOGIC
        # ========================================
        def add_to_cart(product):
            existing = next((item for item in cart if item['product_id'] == product.id), None)
            if product.stock_quantity <= 0:
                ui.notify(f'Sản phẩm {product.name} đã hết hàng!', color='negative')
                return
            if existing:
                existing['quantity'] += 1
            else:
                cart.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': 1
                })
            refresh_cart()
            ui.notify(f'Đã thêm {product.name} vào giỏ', color='positive')

        def update_quantity(product_id, delta):
            idx = next((i for i, item in enumerate(cart) if item['product_id'] == product_id), -1)
            if idx > -1:
                cart[idx]['quantity'] += delta
                if cart[idx]['quantity'] <= 0:
                    cart.pop(idx)
                refresh_cart()

        def clear_cart_action():
            if len(cart) > 0:
                cart.clear()
                refresh_cart()
                ui.notify('Đã xóa giỏ hàng', color='warning')

        async def checkout():
            if len(cart) == 0:
                ui.notify('Không thể thanh toán, giỏ hàng đang trống!', color='negative')
                return
            order_data = schemas.OrderCreate(
                customer_id=None,
                items=[schemas.OrderItemCreate(product_id=item['product_id'], quantity=item['quantity']) for item in cart],
                discount=Decimal('0'),
                tax_rate=Decimal('0.1'),
                payment_method='Cash'
            )
            try:
                async with AsyncSessionLocal() as db:
                    result = await crud.create_order(db=db, order_data=order_data, user_id=1)
                ui.notify(f'🎉 Thanh toán Thành Công! Tạo Đơn Số #{result.id}', color='positive')
                cart.clear()
                refresh_cart()
                refresh_products()
            except Exception as e:
                detail = str(e)
                if hasattr(e, 'detail'):
                    detail = e.detail
                ui.notify(f'Lỗi: {detail}', color='negative')

        # ========================================
        # INVENTORY ACTIONS
        # ========================================
        async def restock_product(product_id, product_name):
            with ui.dialog() as dialog, ui.card().style('border-radius: 24px; padding: 24px; min-width: 380px;'):
                ui.label(f'📦 Nhập hàng: {product_name}').style('font-size: 18px; font-weight: 700; margin-bottom: 20px;')
                
                with ui.column().classes('w-full gap-1'):
                    ui.label('Số lượng nhập thêm').style('font-weight: 600; color: var(--md-text-secondary); margin-left: 4px;')
                    qty_input = ui.input(placeholder='Ví dụ: 10').props('outlined type=number').classes('w-full').style('font-size: 16px;')
                    qty_input.value = 10
                with ui.row().style('justify-content: flex-end; gap: 12px; margin-top: 16px; width: 100%;'):
                    ui.button('Hủy', on_click=dialog.close).props('flat').style('color: var(--md-text-secondary);')
                    async def do_restock():
                        qty = int(qty_input.value)
                        if qty <= 0:
                            ui.notify('Số lượng không hợp lệ!', color='negative')
                            return
                        try:
                            async with AsyncSessionLocal() as db:
                                await crud.restock_inventory(db=db, product_id=product_id, quantity=qty, user_id=1)
                            ui.notify(f'Đã nhập thêm +{qty} cho {product_name}!', color='positive')
                            dialog.close()
                            refresh_inventory()
                        except Exception as e:
                            detail = str(e)
                            if hasattr(e, 'detail'):
                                detail = e.detail
                            ui.notify(f'Lỗi: {detail}', color='negative')
                    ui.button('Xác nhận', on_click=do_restock).style(
                        'background: linear-gradient(to right, var(--md-primary), #8e24aa); color: white; '
                        'border-radius: 12px; padding: 10px 24px; font-weight: 600;'
                    )
            dialog.open()

        async def open_add_product_modal():
            with ui.dialog() as dialog, ui.card().style('border-radius: 24px; padding: 0; width: 500px; max-width: 95vw; overflow: hidden;'):
                # Header
                with ui.element('div').classes('w-full').style('padding: 24px; border-bottom: 1px solid var(--md-divider); display: flex; justify-content: space-between; align-items: center;'):
                    ui.label('Thêm Mặt Hàng Mới').style('font-size: 20px; font-weight: 700;')
                    ui.button(icon='close', on_click=dialog.close).props('flat round dense').style('color: var(--md-text-secondary);')
                # Body
                with ui.element('div').classes('w-full items-stretch column gap-5').style('padding: 24px;'):
                    # Field 1
                    with ui.column().classes('w-full gap-1'):
                        ui.label('Tên Mặt Hàng').style('font-weight: 600; color: var(--md-text-secondary); margin-left: 4px;')
                        name_input = ui.input(placeholder='Ví dụ: Nước giải khát').props('outlined').classes('w-full').style('font-size: 16px;')
                    
                    # Field 2
                    with ui.column().classes('w-full gap-1'):
                        ui.label('Giá Bán (VNĐ)').style('font-weight: 600; color: var(--md-text-secondary); margin-left: 4px;')
                        price_input = ui.input(placeholder='Ví dụ: 15000').props('outlined type=number').classes('w-full').style('font-size: 16px;')
                    
                    # Field 3
                    with ui.column().classes('w-full gap-1'):
                        ui.label('Số Lượng Khởi Tạo').style('font-weight: 600; color: var(--md-text-secondary); margin-left: 4px;')
                        qty_input = ui.input(placeholder='Ví dụ: 50').props('outlined type=number').classes('w-full').style('font-size: 16px;')
                        qty_input.value = 0
                # Footer
                with ui.element('div').classes('w-full flex justify-end items-center').style('padding: 16px 24px; border-top: 1px solid var(--md-divider); background: #fafafa;'):
                    ui.button('Hủy', on_click=dialog.close).props('flat').style('color: var(--md-text-secondary); margin-right: 12px;')
                    async def submit_product():
                        name = name_input.value.strip() if name_input.value else ''
                        price = price_input.value
                        quantity = qty_input.value
                        if not name or not price or quantity is None:
                            ui.notify('Vui lòng điền đầy đủ thông tin!', color='negative')
                            return
                        if float(price) <= 0:
                            ui.notify('Giá phải lớn hơn 0!', color='negative')
                            return
                        try:
                            product_in = schemas.ProductCreate(name=name, price=Decimal(str(price)), stock_quantity=int(quantity))
                            async with AsyncSessionLocal() as db:
                                await crud.create_product(db=db, product_in=product_in)
                            ui.notify(f'🎉 Đã tạo mặt hàng [{name}] thành công!', color='positive')
                            dialog.close()
                            refresh_inventory()
                            refresh_products()
                        except Exception as e:
                            detail = str(e)
                            if hasattr(e, 'detail'):
                                detail = e.detail
                            ui.notify(f'Lỗi: {detail}', color='negative')
                    ui.button('Đăng Ký', on_click=submit_product).props('elevated').style(
                        'background: linear-gradient(to right, var(--md-primary), #8e24aa); color: white; '
                        'border-radius: 12px; padding: 10px 32px; font-weight: 700;'
                    )
            dialog.open()

        # ========================================
        # INVOICES ACTIONS
        # ========================================
        async def clear_all_invoices():
            with ui.dialog() as dialog, ui.card().style('border-radius: 24px; padding: 24px; min-width: 400px;'):
                ui.label('⚠️ Cảnh báo').style('font-size: 20px; font-weight: 700; color: #d32f2f; margin-bottom: 8px;')
                ui.label('Bạn có chắc chắn muốn xóa vĩnh viễn toàn bộ lịch sử hóa đơn? Hành động này không thể hoàn tác!').style('color: var(--md-text-secondary); margin-bottom: 16px;')
                with ui.row().style('justify-content: flex-end; gap: 12px; width: 100%;'):
                    ui.button('Hủy', on_click=dialog.close).props('flat').style('color: var(--md-text-secondary);')
                    async def do_clear():
                        try:
                            async with AsyncSessionLocal() as db:
                                await crud.clear_all_invoices(db)
                            ui.notify('🗑 Đã xóa toàn bộ lịch sử hóa đơn!', color='warning')
                            dialog.close()
                            refresh_invoices()
                        except Exception as e:
                            ui.notify(f'Lỗi: {str(e)}', color='negative')
                    ui.button('Xóa tất cả', on_click=do_clear).style(
                        'background: #d32f2f; color: white; border-radius: 12px; padding: 10px 24px; font-weight: 600;'
                    )
            dialog.open()

        def show_invoice_details(order):
            with ui.dialog() as dialog, ui.card().style('border-radius: 24px; padding: 0; width: 650px; max-width: 95vw; overflow: hidden;'):
                # Header
                with ui.element('div').classes('w-full').style('padding: 24px; border-bottom: 1px solid var(--md-divider); display: flex; justify-content: space-between; align-items: center;'):
                    ui.label(f'Chi Tiết Hóa Đơn #{order.id}').style('font-size: 20px; font-weight: 700;')
                    ui.button(icon='close', on_click=dialog.close).props('flat round dense').style('color: var(--md-text-secondary);')
                # Body
                with ui.element('div').classes('w-full items-stretch column').style('padding: 24px;'):
                    # Meta info
                    from datetime import datetime
                    date_str = order.created_at.strftime('%d/%m/%Y %H:%M:%S') if order.created_at else ''
                    with ui.element('div').classes('w-full flex justify-between').style('margin-bottom: 20px; color: #5f6368;'):
                        ui.label(f'Ngày tạo: {date_str}')
                        ui.label(f'Thanh toán: {order.payment_method or "Tiền mặt"}')
                    # Items table
                    with ui.element('table').classes('detail-table w-full').style('border-collapse: collapse;'):
                        with ui.element('thead'):
                            with ui.element('tr'):
                                el('th', 'Sản phẩm')
                                el('th', 'Đơn giá', style='text-align: right;')
                                el('th', 'SL', style='text-align: center;')
                                el('th', 'Thành tiền', style='text-align: right;')
                        with ui.element('tbody'):
                            for item in order.items:
                                p = next((p for p in products_db if p.id == item.product_id), None)
                                name = p.name if p else f'SP #{item.product_id}'
                                with ui.element('tr'):
                                    el('td', name)
                                    el('td', format_currency(item.unit_price), style='text-align: right;')
                                    el('td', str(item.quantity), style='text-align: center;')
                                    el('td', format_currency(item.subtotal), style='text-align: right; font-weight: 500;')
                    # Summary
                    with ui.element('div').classes('w-full').style('margin-top: 20px; border-top: 2px dashed #eee; padding-top: 15px;'):
                        with ui.element('div').classes('w-full flex justify-between').style('margin-bottom: 5px;'):
                            ui.label('Tổng tiền hàng:')
                            ui.label(format_currency(order.total_amount))
                        with ui.element('div').classes('w-full flex justify-between').style('margin-bottom: 5px; color: #d32f2f;'):
                            ui.label('Giảm giá:')
                            ui.label(f'- {format_currency(order.discount)}')
                        with ui.element('div').classes('w-full flex justify-between').style('margin-top: 10px; font-size: 1.2em; font-weight: bold; color: var(--md-primary);'):
                            ui.label('TỔNG CỘNG:')
                            ui.label(format_currency(order.final_amount))
                # Footer
                with ui.element('div').style('padding: 16px 24px; border-top: 1px solid var(--md-divider); display: flex; justify-content: flex-end; background: #fafafa;'):
                    ui.button('Đã Hiểu', on_click=dialog.close).props('elevated').style(
                        'background: linear-gradient(to right, var(--md-primary), #8e24aa); color: white; '
                        'border-radius: 12px; padding: 10px 32px; font-weight: 700;'
                    )
            dialog.open()

        # ========================================
        # REFRESHABLE UI SECTIONS
        # ========================================
        @ui.refreshable
        async def render_products_grid():
            await load_products_data()
            if not products_db:
                with ui.element('div').style('padding: 20px; color: #5f6368;'):
                    ui.label('Không có sản phẩm nào. Hãy thêm mới!')
                return
            for product in products_db:
                is_out = product.stock_quantity <= 0
                icon = 'inventory_2'
                if hasattr(product, 'sku') and product.sku:
                    if 'FOO' in product.sku or 'SNC' in product.sku:
                        icon = 'fastfood'
                    elif 'DRK' in product.sku:
                        icon = 'local_cafe'

                card = ui.element('div').classes(f'product-card elevation-1{"  out-of-stock" if is_out else ""}')
                card.on('click', lambda p=product: add_to_cart(p))
                with card:
                    with ui.element('div').classes('product-img'):
                        ui.html(f'<span class="material-symbols-rounded">{icon}</span>')
                    with ui.element('div').classes('product-info'):
                        el('div', product.name, classes='product-name')
                        el('div', format_currency(product.price), classes='product-price')
                        stock_cls = 'in-stock' if product.stock_quantity > 0 else 'out-of-stock'
                        el('div', f'Kho còn: {product.stock_quantity}', classes=f'stock-indicator {stock_cls}')

        @ui.refreshable
        def render_cart_section():
            # Cart items
            with ui.element('div').classes('cart-items'):
                if len(cart) == 0:
                    with ui.element('div').classes('empty-cart-msg'):
                        ui.html('<span class="material-symbols-rounded" style="font-size: 48px; opacity: 0.3;">shopping_basket</span>')
                        ui.html('<p style="margin-top: 10px;">Chưa chọn sản phẩm nào</p>')
                else:
                    for item in cart:
                        with ui.element('div').classes('cart-item elevation-1'):
                            with ui.element('div').classes('item-visual'):
                                ui.html('<span class="material-symbols-rounded" style="color:#9e9e9e;">receipt_long</span>')
                            with ui.element('div').classes('item-details'):
                                el('div', item['name'], classes='item-name')
                                el('div', format_currency(item['price']), classes='item-price')
                            with ui.element('div').classes('item-actions'):
                                minus_btn = el('button', '−', classes='qty-btn')
                                minus_btn.on('click', lambda pid=item['product_id']: update_quantity(pid, -1))
                                ui.html(f'<span style="font-weight:700; width: 24px; text-align: center; color: var(--md-text-primary);">{item["quantity"]}</span>')
                                plus_btn = el('button', '+', classes='qty-btn')
                                plus_btn.on('click', lambda pid=item['product_id']: update_quantity(pid, 1))

            # Cart summary
            subtotal = sum(item['price'] * item['quantity'] for item in cart)
            tax = subtotal * 0.1
            total = subtotal + tax

            with ui.element('div').classes('cart-summary'):
                with ui.element('div').classes('summary-row'):
                    ui.label('Tạm tính')
                    ui.label(format_currency(subtotal))
                with ui.element('div').classes('summary-row'):
                    ui.label('Thuế (10%)')
                    ui.label(format_currency(tax))
                with ui.element('div').classes('summary-row total-row'):
                    ui.label('Tổng cộng')
                    ui.label(format_currency(total)).style('color: var(--md-primary);')
                checkout_btn = ui.element('button').classes('md-button primary full-width')
                checkout_btn.on('click', checkout)
                with checkout_btn:
                    ui.html('<span class="material-symbols-rounded">credit_card</span>')
                    ui.html('Xác nhận thanh toán')

        @ui.refreshable
        async def render_inventory_table():
            await load_products_data()
            with ui.element('div').classes('elevation-1').style('background: white; border-radius: 12px; overflow: hidden;'):
                with ui.element('table').classes('md-table'):
                    with ui.element('thead'):
                        with ui.element('tr'):
                            el('th', 'Mã SKU')
                            el('th', 'Tên Sản Phẩm')
                            el('th', 'Giá Bán')
                            el('th', 'Tồn Kho')
                            el('th', 'Trạng Thái')
                    with ui.element('tbody'):
                        for item in products_db:
                            with ui.element('tr'):
                                el('td', item.sku, style='font-weight: 500;')
                                el('td', item.name)
                                el('td', format_currency(item.price))
                                stock_color = '#d32f2f' if item.stock_quantity < item.min_stock_level else 'inherit'
                                el('td', str(item.stock_quantity), style=f'font-weight: bold; color: {stock_color};')
                                with ui.element('td'):
                                    btn = el('button', 'Nhập Hàng', classes='action-btn')
                                    btn.on('click', lambda pid=item.id, pname=item.name: restock_product(pid, pname))

        @ui.refreshable
        async def render_invoices_table():
            await load_invoices_data()
            with ui.element('div').classes('elevation-1').style('background: white; border-radius: 12px; overflow: hidden;'):
                with ui.element('table').classes('md-table'):
                    with ui.element('thead'):
                        with ui.element('tr'):
                            el('th', 'Mã HD')
                            el('th', 'Thời Gian Tạo')
                            el('th', 'Sản Phẩm')
                            el('th', 'Tổng Tiền')
                            el('th', 'Trạng Thái')
                    with ui.element('tbody'):
                        if not invoices_data:
                            with ui.element('tr'):
                                td = ui.element('td').style('text-align: center; padding: 40px; color: #5f6368;')
                                td._text = 'Chưa có hóa đơn nào'
                                td.props('colspan="5"')
                        for order in invoices_data:
                            date_str = order.created_at.strftime('%d/%m/%Y %H:%M:%S') if order.created_at else ''
                            row = ui.element('tr').style('cursor: pointer;')
                            row.on('click', lambda o=order: show_invoice_details(o))
                            with row:
                                el('td', f'#{order.id}', style='font-weight: 500;')
                                el('td', date_str, style='color: #5f6368;')
                                el('td', f'... {len(order.items)} mặt hàng')
                                el('td', format_currency(order.final_amount), style='font-weight: bold; color: var(--md-primary);')
                                with ui.element('td'):
                                    el('span', 'Thành Công', classes='status-chip success')

        # Helper refresh functions
        def refresh_products():
            render_products_grid.refresh()

        def refresh_cart():
            render_cart_section.refresh()

        def refresh_inventory():
            render_inventory_table.refresh()

        def refresh_invoices():
            render_invoices_table.refresh()

        # ========================================
        # BUILD THE LAYOUT
        # ========================================
        nav_buttons = []

        with ui.element('div').classes('app-container'):
            # ---- SIDEBAR ----
            with ui.element('aside').classes('sidebar elevation-2'):
                with ui.element('div').classes('sidebar-header'):
                    ui.html('<span class="material-symbols-rounded logo-icon">storefront</span>')
                    ui.html('<h2 style="font-size: 16px; line-height: 1.2;">HoaPhat Store<br>Management</h2>')
                with ui.element('nav').classes('sidebar-nav'):
                    # POS tab
                    pos_btn = ui.element('button').classes('nav-item active')
                    pos_btn.on('click', lambda: switch_tab('pos'))
                    with pos_btn:
                        ui.html('<span class="material-symbols-rounded">point_of_sale</span>')
                        ui.html('Bán Hàng (POS)')
                    nav_buttons.append({'id': 'pos', 'element': pos_btn})

                    # Inventory tab
                    inv_btn = ui.element('button').classes('nav-item')
                    inv_btn.on('click', lambda: switch_tab('inventory'))
                    with inv_btn:
                        ui.html('<span class="material-symbols-rounded">inventory_2</span>')
                        ui.html('Tồn Kho')
                    nav_buttons.append({'id': 'inventory', 'element': inv_btn})

                    # Invoices tab
                    invoices_btn = ui.element('button').classes('nav-item')
                    invoices_btn.on('click', lambda: switch_tab('invoices'))
                    with invoices_btn:
                        ui.html('<span class="material-symbols-rounded">receipt_long</span>')
                        ui.html('Hóa Đơn')
                    nav_buttons.append({'id': 'invoices', 'element': invoices_btn})

            # ---- MAIN CONTENT ----
            with ui.element('main').classes('main-content'):
                # App Bar
                with ui.element('header').classes('app-bar elevation-1'):
                    with ui.element('div').classes('search-bar'):
                        ui.input(placeholder='Tìm kiếm mặt hàng, hóa đơn...').props('rounded standout dense borderless').classes('full-width').style('font-size: 15px;')\
                            .add_slot('prepend', '<span class="material-symbols-rounded" style="color: var(--md-text-secondary)">search</span>')
                    with ui.element('div').classes('user-profile'):
                        ui.html('<span class="material-symbols-rounded" style="cursor: pointer; color:#5f6368;">notifications</span>')
                        ui.html('<div class="avatar elevation-1">AD</div>')
                        ui.html('<span style="font-weight: 500;">Admin</span>')

                # ---- POS VIEW ----
                pos_view_ref = ui.element('div').classes('view-section active').style('display: block;')
                with pos_view_ref:
                    with ui.element('div').classes('pos-layout'):
                        # Products area
                        with ui.element('div').classes('products-area'):
                            ui.html('<h2 class="section-title">Danh mục Sản phẩm</h2>')
                            with ui.element('div').classes('category-tabs'):
                                ui.html('<button class="md-chip active">Tất cả</button>')
                                ui.html('<button class="md-chip">Thực phẩm</button>')
                                ui.html('<button class="md-chip">Đồ gia dụng</button>')
                            with ui.element('div').classes('products-grid'):
                                render_products_grid()

                        # Cart sidebar
                        with ui.element('div').classes('cart-sidebar elevation-3'):
                            with ui.element('div').classes('cart-header'):
                                ui.html('<h2>Giỏ hàng hiện tại</h2>')
                                delete_btn = ui.element('button').classes('btn-icon')
                                delete_btn.on('click', clear_cart_action)
                                with delete_btn:
                                    ui.html('<span class="material-symbols-rounded">delete</span>')
                            render_cart_section()

                # ---- INVENTORY VIEW ----
                inv_view_ref = ui.element('div').classes('view-section').style('display: none; padding: 24px;')
                with inv_view_ref:
                    with ui.element('div').style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'):
                        ui.html('<h1 class="page-title" style="margin-bottom: 0;">Quản lý Tồn Kho</h1>')
                        with ui.element('div').classes('header-actions'):
                            add_btn = ui.element('button').classes('header-btn secondary')
                            add_btn.on('click', open_add_product_modal)
                            with add_btn:
                                ui.html('<span class="material-symbols-rounded">add</span>')
                                ui.html('Thêm Mới')
                            refresh_inv_btn = ui.element('button').classes('header-btn primary')
                            refresh_inv_btn.on('click', lambda: (refresh_inventory(), ui.notify('Đã làm mới Tồn Kho!', color='positive')))
                            with refresh_inv_btn:
                                ui.html('<span class="material-symbols-rounded">refresh</span>')
                                ui.html('Làm mới')
                    render_inventory_table()

                # ---- INVOICES VIEW ----
                invoices_view_ref = ui.element('div').classes('view-section').style('display: none; padding: 24px;')
                with invoices_view_ref:
                    with ui.element('div').style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'):
                        ui.html('<h1 class="page-title" style="margin-bottom: 0;">Lịch sử Hóa Đơn</h1>')
                        with ui.element('div').classes('header-actions'):
                            clear_inv_btn = ui.element('button').classes('header-btn danger')
                            clear_inv_btn.on('click', clear_all_invoices)
                            with clear_inv_btn:
                                ui.html('<span class="material-symbols-rounded">delete_sweep</span>')
                                ui.html('Xóa tất cả')
                            refresh_invoices_btn = ui.element('button').classes('header-btn primary')
                            refresh_invoices_btn.on('click', lambda: (refresh_invoices(), ui.notify('Đã làm mới Lịch Sử Hóa Đơn!', color='positive')))
                            with refresh_invoices_btn:
                                ui.html('<span class="material-symbols-rounded">refresh</span>')
                                ui.html('Làm mới')
                    render_invoices_table()
