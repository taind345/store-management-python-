# HoaPhat Store Management (Hệ Thống Quản Lý Cửa Hàng HoaPhát)

Dự án này là một hệ thống quản lý bán hàng chuyên nghiệp, được xây dựng hoàn toàn bằng **Python**. Hệ thống kết hợp sức mạnh của **FastAPI** (Backend API) và sự linh hoạt của **NiceGUI** (Frontend UI) để tạo ra một trải nghiệm ứng dụng web hiện đại theo phong cách Material Design 3.

Dưới đây là hướng dẫn chi tiết để thiết lập và khởi chạy toàn bộ hệ thống trên môi trường Windows.

---

## 1. Yêu cầu hệ thống (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
- **Python** (Phiên bản >= 3.9). Kiểm tra bằng lệnh: `python --version`
- **PostgreSQL**: Hệ quản trị cơ sở dữ liệu.
- **pgAdmin 4**: Công cụ quản lý PostgreSQL (khuyến nghị).

---

## 2. Thiết lập Cơ sở dữ liệu (Database Setup)

Chuỗi kết nối mặc định (trong file `app/database.py`):
`postgresql+asyncpg://postgres:postgres@localhost:5432/sales_db`

**Các bước thực hiện:**
1. Mở **pgAdmin 4**.
2. Tạo một Database mới với tên: **`sales_db`**.
3. *Lưu ý: Nếu thông tin tài khoản PostgreSQL của bạn khác với `postgres`/`postgres`, hãy cập nhật lại chuỗi kết nối trong `app/database.py`.*

---

## 3. Cài đặt và Khởi chạy Hệ thống

Hệ thống hiện đã được hợp nhất. Bạn chỉ cần chạy một lệnh duy nhất để khởi động cả Backend và Frontend.

**Các bước thực hiện trong Terminal/PowerShell:**

```bash
# 1. Di chuyển vào thư mục dự án
cd banhang

# 2. Tạo Môi trường Ảo (Virtual Environment)
python -m venv venv

# 3. Kích hoạt môi trường ảo
.\venv\Scripts\activate

# 4. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 5. Khởi chạy toàn bộ hệ thống
python run.py
```

> **Thành công:** Sau khi chạy lệnh cuối cùng, trình duyệt của bạn sẽ tự động mở địa chỉ **[http://localhost:8000](http://localhost:8000)**. Đây là giao diện quản lý chính của cửa hàng.

---

## 4. Các tính năng chính

Hệ thống cung cấp giao diện Material Design 3 đồng nhất với các chức năng:
- **Bán Hàng (POS)**: Giao diện tính tiền trực quan, hỗ trợ tìm kiếm và giỏ hàng thời gian thực.
- **Quản Lý Tồn Kho**: Theo dõi lượng hàng, thêm mới mặt hàng và nhập hàng (restock).
- **Lịch Sử Hóa Đơn**: Xem chi tiết các giao dịch đã thực hiện, quản lý doanh thu.

---

## 5. Hướng dẫn sử dụng lại (Sau khi tắt máy)

Khi bạn muốn chạy lại hệ thống vào lần sau:
1. Mở Terminal tại thư mục dự án.
2. Kích hoạt môi trường ảo: `.\venv\Scripts\activate`
3. Chạy lệnh: `python run.py`

---

## 6. Mô tả Hệ thống (System Description)

Hệ thống được thiết kế theo kiến trúc tách biệt giữa **Core Logic (Backend)** và **User Interface (Frontend)**, tất cả đều được viết bằng ngôn ngữ Python.

### 6.1. Cấu trúc Dự án (Project Structure)

```text
banhang/
├── app/                      # Backend Logic (FastAPI)
│   ├── crud.py               # Thao tác CSDL (Create, Read, Update, Delete)
│   ├── database.py           # Kết nối PostgreSQL (SQLAlchemy Async)
│   ├── main.py               # Định nghĩa các API Endpoints
│   ├── models.py             # Khai báo cấu trúc bảng CSDL (ORM)
│   └── schemas.py            # Định nghĩa kiểu dữ liệu Input/Output (Pydantic)
├── frontend_python/          # Frontend Logic (NiceGUI)
│   └── ui_app.py             # Giao diện người dùng & Logic xử lý UI
├── run.py                    # Script khởi chạy đồng bộ Backend & Frontend
├── seed.py                   # Tạo dữ liệu mẫu ban đầu cho hệ thống
├── reset_db.py               # Xóa và khởi tạo lại toàn bộ Cơ sở dữ liệu
├── fix_db_sequence.py        # Sửa lỗi nhảy ID (Serial Sequence) trong DB
├── requirements.txt          # Danh sách thư viện phụ thuộc
└── README.md                 # Tài liệu hướng dẫn dự án
```

### 6.2. Các Thành phần và Hàm Chức năng Chính

#### 1. Backend API (Thư mục `app/`)
Đây là bộ não của hệ thống, xử lý các phép toán và lưu trữ dữ liệu thông qua cơ chế bất đồng bộ (**Async/Await**).
- **`models.py`**: Định nghĩa cấu trúc Schema trong PostgreSQL. 
    - Bao gồm các bảng: `Category`, `Product`, `Order`, `OrderItem`, và `InventoryLog` (để truy vết lịch sử nhập xuất).
    - Sử dụng các mối quan hệ `relationship` (One-to-Many) giữa Order và OrderItem để quản lý chi tiết đơn hàng.
- **`crud.py` (Xử lý nghiệp vụ chính)**:
    - **`create_order`**: Hàm phức tạp nhất. Nó thực hiện:
        1. Sử dụng **Pessimistic Locking** (`with_for_update`) để khóa các dòng sản phẩm trong DB, ngăn chặn lỗi "bán vượt mức tồn kho" khi 2 nhân viên cùng nhấn thanh toán 1 sản phẩm cuối cùng đồng thời.
        2. Tự động tính toán Thuế (Tax), Giảm giá (Discount) và Tổng tiền cuối cùng.
        3. Ghi nhận lịch sử vào bảng `InventoryLog` để quản trị viên có thể kiểm tra lại sau này.
    - **`get_inventory` & `get_invoices`**: Truy vấn bất đồng bộ sử dụng `selectinload` để tải dữ liệu liên quan (Eager Loading), giúp tối ưu hóa hiệu năng (tránh lỗi N+1 Query).
    - **`restock_inventory`**: Xử lý nhập hàng, cập nhật số lượng tồn kho và lưu vết người thực hiện.
- **`schemas.py`**: Sử dụng `Pydantic` để thực hiện **Data Validation**. Đảm bảo dữ liệu đầu vào (ví dụ: giá cả phải là số dương) luôn chính xác trước khi đưa vào Database.

#### 2. Frontend UI (Thư mục `frontend_python/`)
Xây dựng giao diện Single-Page Application (SPA) hiện đại với **NiceGUI** và **Tailwind CSS**.
- **`ui_app.py` (Quản lý trạng thái và giao diện)**:
    - **State Management**: Sử dụng các biến `nonlocal` (như `cart`, `products_db`) để quản lý trạng thái ứng dụng ngay tại phía Client.
    - **`@ui.refreshable`**: Đây là kỹ thuật cốt lõi. Khi dữ liệu thay đổi (như thêm hàng vào giỏ), chỉ phần giao diện liên quan (`render_cart_section`) được cập nhật lại mà không cần tải lại toàn bộ trang web.
    - **Chức năng POS (Bán hàng)**:
        - `add_to_cart`: Kiểm tra tồn kho thời gian thực trước khi cho phép thêm măt hàng.
        - `search_query`: Tích hợp `debounce` để tìm kiếm sản phẩm mượt mà, chỉ gửi yêu cầu sau khi người dùng dừng gõ 400ms.
    - **Hệ thống Dialog & Modal**:
        - Sử dụng `ui.dialog` để tạo các form nhập liệu chuyên nghiệp (Thêm sản phẩm, Nhập hàng, Chỉnh sửa thông tin) với thiết kế bo góc, đổ bóng theo phong cách hiện đại.
    - **Thiết kế Aesthetic**: Sử dụng tông màu kem/đất (Cream/Earth Tones), font chữ Inter và Material Symbols để tạo cảm giác cao cấp, nhẹ nhàng.

#### 3. Scripts Tiện ích
- **`run.py`**: Sử dụng `multiprocessing` hoặc `threading` để khởi động server Backend và UI cùng lúc.
- **`seed.py`**: Tự động nạp vào Database một danh sách sản phẩm mẫu để người dùng có thể test hệ thống ngay lập tức.
- **`reset_db.py` / `fix_db_sequence.py`**: Các công cụ hỗ trợ bảo trì Database trong quá trình phát triển.
