# 🗺 Bản đồ Dự án: Store Management (HoaPhát)

Tài liệu này cung cấp cái nhìn tổng quan về kiến trúc và cấu trúc thư mục của dự án. Hệ thống được thiết kế theo tư duy **Fullstack Python**, tách biệt rõ phần giao diện (Frontend) và phần logic phía sau (Backend), giúp dễ dàng định vị khi tìm và sửa lỗi.

## 📁 Sơ đồ Cây (Project Tree)

```text
banhang/
├── 📄 run.py                   # 🚀 ENTRY POINT: Tập tin gốc khởi động server Uvicorn, chạy đồng thời cả FastAPI và NiceGUI.
├── 📄 requirements.txt         # 📦 Danh sách các module thư viện cần thiết.
├── 📄 reset_db.py              # 🛠 Công cụ: Xóa toàn bộ Database và cấu trúc lại bảng từ đầu.
├── 📄 fix_db_sequence.py       # 🛠 Công cụ: Sửa lỗi đánh số thự tự ID tự tăng (Sequence) của Database.
├── 📄 seed.py                  # 🛠 Công cụ: Sinh dữ liệu chạy thử (Mock data) như Sản Phẩm, Đơn Hàng...
│
├── frontend_python/            # 🎨 FRONTEND (Giao Diện Chức Năng Bán Hàng)
│   ├── 📄 __init__.py          # 
│   └── 📄 ui_app.py            # 💻 Toàn bộ code giao diện (POS, Giỏ Hàng, Danh sách Hóa đơn, Tailwind classes).
│
├── app/                        # ⚙️ BACKEND (Xử lý nghiệp vụ và Cơ Sở Dữ Liệu)
│   ├── 📄 main.py              # Định nghĩa FastAPI app, cấu hình Middleware và tích hợp NiceGUI vào FastAPI.
│   ├── 📄 database.py          # Quản lý kết nối với Database (Thiết lập chuỗi kết nối SQLAlchemy).
│   ├── 📄 schemas.py           # Chứa Pydantic Classes để kiểm tra/validate dữ liệu đầu vào & đầu ra (Kiểm soát lỗi data).
│   ├── 📄 models.py            # Định nghĩa các Bảng trong CSDL (Users, Products, Orders, OrderItems).
│   └── 📄 crud.py              # Các hàm lõi giao tiếp trực tiếp với DB (Create, Read, Update, Delete). Ví dụ: create_order(), get_inventory().
│
└── venv/                       # 🐍 (Môi trường ảo) Chứa mã nguồn các thư viện Python cài từ requirements.txt.
```

---

## 🧭 Cẩm nang Review & Fix Lỗi (Cheat Sheet)

Để tiết kiệm thời gian, khi bạn gặp một tác vụ hay một lỗi nào đó, hãy phân loại lỗi dựa vào **luồng đi của ứng dụng (Data Flow)**:

1. **Lỗi hiển thị, màu sắc, vị trí nút bấm, bố cục vỡ (Layout)**
   👉 Chỉ tìm trong `frontend_python/ui_app.py`.

2. **Lỗi logic không lưu được dữ liệu vào hệ thống, hoặc tính toán sai quy trình kinh doanh**
   👉 Thường nằm ở `app/crud.py` (nơi chứa các thuật toán thao tác Database).

3. **Lỗi liên quan đến thiếu cột, lỗi kiểu dữ liệu (vd: cần int nhưng nhập string)**
   👉 Cần kiểm tra đối chiếu giữa `app/schemas.py` (Đầu vào form) và `app/models.py` (Đích đến ở Database).

4. **App không chạy được lên luôn từ đầu, lỗi Server**
   👉 Kiểm tra từ `run.py` (lệnh khởi chạy) hoặc `app/main.py`.

Mô hình này giúp cho phần Bán Hàng (Frontend) hoàn toàn có thể "bứng" đi và thay bằng một ứng dụng Điện thoại sau này mà không cần đập bỏ đi phần Nhập liệu và Tính toán đã nằm rất gọn ở Backend (`app/`).
