"""
HoaPhat Store Management - Entry Point
Chạy file này để khởi động ứng dụng: python run.py
"""
import uvicorn
from app.main import app as fastapi_app
from frontend_python.ui_app import setup_pages
from nicegui import ui

# Đăng ký các trang NiceGUI
setup_pages()

# Tích hợp NiceGUI vào FastAPI app hiện có
# - Tất cả API endpoints (/orders, /inventory, /invoices, etc.) vẫn hoạt động
# - NiceGUI serve giao diện tại đường dẫn /
ui.run_with(
    fastapi_app,
    title='HoaPhat Store Management | Bán Hàng Trực Tiếp',
    favicon='🏪',
    storage_secret='hoaphat-store-secret-key',
)

if __name__ == '__main__':
    uvicorn.run(fastapi_app, host='0.0.0.0', port=8000)
