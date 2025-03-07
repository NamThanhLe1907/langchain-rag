import sqlite3
from langchain_core.runnables import Runnable, RunnableConfig
from datetime import datetime
from dotenv import load_dotenv
load_dotenv() 

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info = str
    
     

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state, config = config)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
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