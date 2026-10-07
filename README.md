# test-antigravity

Ứng dụng web rút gọn link mini (URL Shortener) viết bằng **Python** sử dụng framework **Flask** và cơ sở dữ liệu **SQLite**.

---

## 🌟 Tính năng chính
- 🔗 **Rút gọn URL**: Tự động sinh mã ngắn ngẫu nhiên gồm 6 ký tự.
- ⚡ **Chuyển hướng tức thì**: Truy cập mã rút gọn sẽ tự động chuyển hướng đến liên kết gốc.
- 📊 **Thống kê Click**: Đếm số lượt truy cập cho từng liên kết.
- 📋 **Sao chép nhanh**: Nút sao chép tiện lợi ngay trên giao diện web.
- 🛠️ **REST API**: Hỗ trợ endpoint `/api/shorten` và `/api/stats/<short_code>`.

---

## 🚀 Hướng dẫn cài đặt và chạy

### 1. Cài đặt thư viện
```bash
pip install flask
```

### 2. Khởi chạy ứng dụng
```bash
python app.py
```

Ứng dụng sẽ chạy tại địa chỉ: `http://127.0.0.1:5000`
