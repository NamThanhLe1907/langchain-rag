# Sử dụng Python 3.11 slim để tối ưu kích thước image
FROM python:3.11-slim

# Cập nhật hệ thống & cài đặt dependencies cơ bản
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Thiết lập user để tránh chạy container bằng root
RUN useradd -m python
USER python

# Sao chép requirements.txt vào container trước để cache nếu không có thay đổi
COPY --chown=python:python requirements.txt .

# Cài đặt dependencies với cache để giảm thời gian build
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ project vào container
COPY --chown=python:python . .

# Thiết lập biến môi trường
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Command mặc định khi chạy container
CMD ["bash"]
