import sqlite3
import uuid
from langchain_core.runnables import Runnable, RunnableConfig
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from typing import TypedDict, Annotated
from langgraph.graph.message import AnyMessage, add_messages


load_dotenv() 

# ✅ Định nghĩa State chung để dùng ở cả Assistant, Graph Builder, Main
class State(TypedDict):
    """✅ State chuẩn có đủ 'messages' và 'user_info'"""
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: dict | str

class Assistant:
    def __init__(self, runnable: Runnable):
        """Khởi tạo Assistant với State mặc định."""
        self.runnable = runnable


    def __call__(self, state: State, config: RunnableConfig):
        """✅ Xử lý Assistant"""
        while True:
            result = self.runnable.invoke(state)
            
    #        print("\n🔍 **DEBUG: AI RESPONSE:**", result)
     #       print("\n🔍 **DEBUG: AI RESPONSE:**", config)
     #       print("🔍 **DEBUG: TOOL CALLS:**", result.tool_calls if hasattr(result, "tool_calls") else "Không có tool calls")

            if hasattr(result, "tool_calls"):
                state["tool_call_ids"] = [tc["id"] for tc in result.tool_calls]
          
            if not result.tool_calls and (not result.content or isinstance(result.content, list) and not result.content[0].get("text")):
                #state["messages"].append(HumanMessage(content="Assistant, vui lòng phản hồi hợp lệ."))
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break  # ✅ Nếu phản hồi hợp lệ, thoát loop
        return {"messages": result}

# ✅ Hàm truy vấn database SQLite
def query_db(query: str):
    """Truy vấn database SQLite và trả về kết quả."""
    conn = sqlite3.connect("travel2.sqlite")  
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results if results else "Không tìm thấy dữ liệu phù hợp."
    except Exception as e:
        conn.close()
        return f"Lỗi truy vấn DB: {str(e)}"
