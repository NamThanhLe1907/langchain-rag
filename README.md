# LangChain RAG

## Giới thiệu
LangChain RAG là một dự án được xây dựng với kiến trúc module rõ ràng, tách biệt logic chính, test cases và cấu hình. Dự án này áp dụng các best practices về cấu trúc thư mục, quy ước đặt tên file (snake_case) và hỗ trợ maintainability, mở rộng về sau.

## Cấu trúc Dự án
```
langchain-rag/
├── src/
│   ├── core/
│   │   ├── assistants/
│   │   │   └── assistants.py      # Logic chính của các assistant
│   │   ├── state.py              # Định nghĩa State (nếu cần mở rộng)
│   │   └── models/               # Các schema, data models
│   ├── utils/
│   │   ├── database.py           # Các hàm truy vấn database
│   │   └── embeddings.py         # Định nghĩa vector store, retriever (nếu cần)
│   └── data/
│       └── repositories/         # Layer truy cập dữ liệu
├── tests/                        # Test cases: unit và integration tests
├── docs/                         # Tài liệu dự án
│   ├── API_REFERENCE.md          # Tài liệu API chi tiết
│   └── TUTORIALS/               # Các hướng dẫn sử dụng và ví dụ
├── configs/                      # File cấu hình (logging, database, ...)
├── examples/                     # Ví dụ sử dụng dự án
├── requirements.txt              # Dependencies sản xuất
├── requirements-dev.txt          # Dependencies phục vụ phát triển và test
├── setup.py                      # Script cài đặt package
├── CONTRIBUTING.md               # Hướng dẫn đóng góp cho dự án
├── .github/
│   └── workflows/
│       └── ci.yml              # Pipeline CI/CD với GitHub Actions
└── README.md                     # File README hiện tại
```

## Cài đặt và Sử dụng

1. **Cài đặt dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Để phát triển và test:**

   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```

3. **Cài đặt package:**

   ```bash
   python setup.py install
   ```

## Pipeline CI/CD
Dự án sử dụng GitHub Actions để tự động chạy linting và kiểm tra unit tests mỗi khi có thay đổi trên nhánh chính:
- **Linting:** Sử dụng `flake8`
- **Testing:** Sử dụng `pytest`

## Hướng dẫn đóng góp
Vui lòng tham khảo file [CONTRIBUTING.md](CONTRIBUTING.md) để biết quy trình đóng góp, coding style và các hướng dẫn cần thiết.

## License
Dự án được cấp phép theo MIT License.
