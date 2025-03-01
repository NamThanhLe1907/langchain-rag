import sqlite3
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from data.state import State
from langchain_openai import ChatOpenAI
from datetime import datetime
from dotenv import load_dotenv
load_dotenv() 

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state, config=config)
            # Kiểm tra nếu kết quả trống thì re-prompt
            if not result.tool_calls and (not result.content or 
                (isinstance(result.content, list) and not result.content[0].get("text"))):
                # Thêm một lời nhắc bổ sung vào state để LLM cho kết quả thực sự
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
    
def query_db(query: str):
        """Truy vấn database SQLite và trả về kết quả."""
        conn = sqlite3.connect("travel2.sqlite")  # Đảm bảo tên file DB đúng
        cursor = conn.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            return results if results else "Không tìm thấy dữ liệu phù hợp."
        except Exception as e:
            conn.close()
            return f"Lỗi truy vấn DB: {str(e)}"