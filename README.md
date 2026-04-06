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

## 6. Cấu trúc thư mục rút gọn

- `app/`: Chứa mã nguồn Backend (FastAPI, CRUD, Database).
- `frontend_python/`: Chứa mã nguồn Giao diện (NiceGUI UI).
- `run.py`: File thực thi chính của toàn bộ hệ thống.
- `requirements.txt`: Danh sách các thư viện Python cần thiết.
