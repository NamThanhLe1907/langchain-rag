# Sử dụng Python 3.11 slim để tối ưu kích thước image
FROM python:3.11-slim

# Cập nhật hệ thống & cài đặt dependencies cơ bản
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Tạo môi trường ảo Python (venv)
RUN python -m venv /app/env

# Kích hoạt venv và cập nhật pip, wheel
RUN /app/env/bin/pip install --no-cache-dir --upgrade pip wheel

# Sao chép requirements.txt vào container
COPY requirements.txt .

# Cài đặt dependencies vào môi trường ảo (venv)
RUN /app/env/bin/pip install --no-cache-dir -r requirements.txt

# Cài đặt python-dotenv để đảm bảo có thể load biến môi trường từ .env
RUN /app/env/bin/pip install --no-cache-dir python-dotenv

# Copy toàn bộ project vào container
COPY . .

# Thiết lập biến môi trường để sử dụng venv
ENV PATH="/app/env/bin:$PATH"

# Copy file .env vào container
COPY .env .env

# Command mặc định khi chạy container
CMD ["bash"]
