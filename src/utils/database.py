import sqlite3

def query_db(query: str, db_path: str = "travel2.sqlite"):
    """Truy vấn database SQLite và trả về kết quả.
    
    Args:
        query (str): Câu lệnh SQL cần thực thi.
        db_path (str): Đường dẫn tới file database (mặc định "travel2.sqlite").
    
    Returns:
        Kết quả của truy vấn hoặc thông báo lỗi nếu có vấn đề xảy ra.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Thêm kiểm tra query và sử dụng parameterized queries
        if not query.strip().lower().startswith(("select", "pragma")):
            raise ValueError("Chỉ hỗ trợ truy vấn SELECT và PRAGMA")
        
        cursor.execute(query, ())  # Sử dụng parameterized query
        results = cursor.fetchall()
        conn.close()
        return results if results else "Không tìm thấy dữ liệu phù hợp."
    except Exception as e:
        conn.close()
        return f"Lỗi truy vấn DB: {str(e)}"