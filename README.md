# Hệ Thống Quản Lý Bán Hàng (Sales Management System)

Dự án này là một Hệ Thống Quản Lý Bán Hàng, bao gồm **Backend API** được xây dựng bằng Python với FastAPI và **Frontend UI** (HTML/JS/CSS) áp dụng phong cách Material Design.

Dưới đây là hướng dẫn chi tiết để thiết lập và khởi chạy toàn bộ hệ thống trên môi trường Windows.

## 1. Yêu cầu hệ thống (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
- **Python** (Phiên bản >= 3.9). Mở Terminal và gõ `python --version` để kiểm tra.
- **PostgreSQL**: Hệ quản trị cơ sở dữ liệu. Khuyến nghị cài đặt kèm công cụ **pgAdmin 4** để dễ dàng thao tác với database.

---

## 2. Thiết lập Cơ sở dữ liệu (Database Setup)

Chuỗi kết nối cơ sở dữ liệu được cấu hình mặc định trong file `app/database.py` như sau:
`postgresql+asyncpg://postgres:postgres@localhost:5432/sales_db`

**Các bước thực hiện:**
1. Mở **pgAdmin 4** (hoặc sử dụng `psql` trong terminal)
2. Tạo một Database mới với tên chính xác là: **`sales_db`**.
3. *Lưu ý: Đảm bảo username và password truy cập PostgreSQL của bạn là `postgres` / `postgres`. Nếu thông tin kết nối máy bạn khác đi, hãy mở file `app/database.py` và cập nhật lại chuỗi kết nối cho phù hợp.*

---

## 3. Khởi chạy Backend (FastAPI)

Backend sẽ tự động tạo các bảng dữ liệu (User, Order, v.v.) trong PostgreSQL ở lần chạy đầu tiên và mở cổng `8000` để bắt đầu nhận các yêu cầu từ giao diện Thu ngân.

Mở **PowerShell / Terminal**, di chuyển vào thư mục của dự án và chạy các lệnh dưới đây:

```bash
# 1. Tạo Môi trường Ảo (Virtual Environment) để quản lý thư viện độc lập
python -m venv venv

# 2. Kích hoạt môi trường ảo (trên Windows)
.\venv\Scripts\activate

# 3. Cài đặt các thư viện cần thiết cho dự án
pip install -r requirements.txt

# 4. Khởi chạy Server FastAPI
uvicorn app.main:app --reload
```

> **Thành công:** Khi Terminal xuất hiện dòng chữ `Application startup complete.`, server đã sẵn sàng hoạt động và các bảng dữ liệu đã được tự động tạo trong DB `sales_db`.

Bạn có thể xem tài liệu API (Swagger UI) và tương tác trực tiếp bằng cách truy cập: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 4. Khởi chạy Frontend (Giao diện Thu ngân/POS)

Giao diện frontend được xây dựng dưới dạng Single Page Application (SPA) tĩnh hoàn chỉnh. Do đó, bạn không cần phải chạy thêm server Node.js hay công cụ tương tự.

**Cách khởi chạy:**
1. Di chuyển vào thư mục `frontend` bên trong dự án.
2. Nhấn đúp chuột hoặc dùng trình duyệt (Google Chrome / Edge / Firefox) để mở trực tiếp file **`index.html`**.

**Kiểm tra hệ thống:**
1. Tại giao diện Thu ngân, hãy thử thêm một vài sản phẩm vào giỏ hàng.
2. Nhấn nút **"Xác Nhận Thanh Toán"**.
3. Nếu bạn thấy thông báo ở góc dưới màn hình *(Ví dụ: "Tạo đơn hàng Số #1 Thành Công")*, xin chúc mừng! Toàn bộ quy trình từ Frontend tương tác xuống Backend và lưu trữ vào Database đã hoạt động trơn tru.

---

## 5. Hướng dẫn chạy lại hệ thống (Sau khi tắt Terminal)

Khi bạn đã tắt Terminal (PowerShell/CMD) tĩnh hoặc khởi động lại máy tính, bạn **không cần cài đặt lại** thư viện hay tạo Database nữa. Chỉ cần thực hiện các bước sau để chạy lại Backend:

1. Mở lại **PowerShell / Terminal**.
2. Di chuyển vào thư mục dự án của bạn:
   ```bash
   # Di chuyển vào thư mục chứa code
   cd đường_dẫn_đến_thư_mục_banhang
   ```
3. Kích hoạt môi trường ảo:
   ```bash
   .\venv\Scripts\activate
   ```
4. Khởi chạy lại Server:
   ```bash
   uvicorn app.main:app --reload
   ```

*Đối với Frontend UI, bạn chỉ cần mở lại file `index.html` trong trình duyệt là có thể tiếp tục sử dụng bình thường.*
