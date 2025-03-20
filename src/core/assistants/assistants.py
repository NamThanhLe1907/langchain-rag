import sqlite3
import uuid
from langchain_core.runnables import Runnable, RunnableConfig
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from typing import TypedDict, Annotated, Optional, Literal
from langgraph.graph.message import AnyMessage, add_messages
from pydantic import BaseModel, Field

load_dotenv()

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

# Hàm truy vấn database SQLite
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

# Định nghĩa State chung để dùng ở cả Assistant, Graph Builder, Main
class State(TypedDict):
    """State chuẩn có đủ 'messages' và 'user_info'"""
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: dict | str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "update_flight",
                "book_car_rental",
                "book_hotel",
                "book_excursion"
            ]
        ],
        update_dialog_stack,
    ]

class Assistant:
    def __init__(self, runnable: Runnable):
        """Khởi tạo Assistant với State mặc định."""
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        """Xử lý Assistant với kiểm tra kiểu dữ liệu của result.content và in debug state."""
        print("===== DEBUG: Vào __call__ của Assistant =====")
        print("Initial state keys:", list(state.keys()))
        print("Initial state dialog_state:", state.get("dialog_state"))
        print("Initial state user_info:", state.get("user_info"))
        print("Initial state messages count:", len(state.get("messages", [])))
        
        while True:
            result = self.runnable.invoke(state)
            print("----- DEBUG: Sau khi invoke runnable -----")
            print("Result type:", type(result))
            if hasattr(result, "tool_calls"):
                print("Result tool_calls:", result.tool_calls)
                state["tool_call_ids"] = [tc["id"] for tc in result.tool_calls]
            
            # Kiểm tra result.content nếu không có tool_calls
            if not result.tool_calls:
                if not result.content:
                    valid_content = False
                    print("DEBUG: result.content rỗng hoặc None")
                elif isinstance(result.content, list):
                    first_item = result.content[0]
                    print("DEBUG: Kiểu của phần tử đầu tiên trong result.content:", type(first_item))
                    # Nếu là dict và có key "text"
                    if isinstance(first_item, dict) and first_item.get("text"):
                        valid_content = True
                        print("DEBUG: result.content hợp lệ (list có dict với key 'text')")
                    else:
                        valid_content = False
                        print("DEBUG: result.content không hợp lệ (list nhưng không chứa dict với key 'text')")
                elif isinstance(result.content, dict):
                    if result.content.get("text"):
                        valid_content = True
                        print("DEBUG: result.content hợp lệ (dict có key 'text')")
                    else:
                        valid_content = False
                        print("DEBUG: result.content không hợp lệ (dict nhưng không có key 'text')")
                elif isinstance(result.content, str):
                    valid_content = bool(result.content.strip())
                    if valid_content:
                        print("DEBUG: result.content hợp lệ (chuỗi không rỗng)")
                    else:
                        print("DEBUG: result.content không hợp lệ (chuỗi rỗng)")
                elif hasattr(result.content, "text"):
                    text_val = getattr(result.content, "text", "").strip()
                    valid_content = bool(text_val)
                    if valid_content:
                        print("DEBUG: result.content hợp lệ (đối tượng có thuộc tính 'text')")
                    else:
                        print("DEBUG: result.content không hợp lệ (đối tượng có thuộc tính 'text' rỗng)")
                else:
                    valid_content = False
                    print("DEBUG: result.content không hợp lệ (không nhận dạng được kiểu)")
                
                if not valid_content:
                    # Thêm một message để yêu cầu đầu ra hợp lệ
                    print("DEBUG: Thêm message yêu cầu đầu ra hợp lệ.")
                    messages = state["messages"] + [("user", "Respond with a real output.")]
                    state = {**state, "messages": messages}
                    print("DEBUG: Số lượng messages hiện tại:", len(state["messages"]))
                    continue
            break  # Nếu có tool_calls hoặc content hợp lệ thì thoát khỏi loop

        print("===== DEBUG: Kết thúc __call__ của Assistant =====")
        print("Final state keys:", list(state.keys()))
        print("Final state dialog_state:", state.get("dialog_state"))
        print("Final state messages count:", len(state.get("messages", [])))
        return {"messages": result}

class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""
    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind về current task."
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task."
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information."
            }
        }

class ToFlightBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""
    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )

class ToBookCarRental(BaseModel):
    """Transfers work to a specialized assistant to handle car rental bookings."""
    location: str = Field(
        description="The location where the user wants to rent a car."
    )
    start_date: str = Field(description="The start date of the car rental.")
    end_date: str = Field(description="The end date of the car rental.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the car rental."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Basel",
                "start_date": "2023-07-01",
                "end_date": "2023-07-05",
                "request": "I need a compact car with automatic transmission."
            }
        }

class ToHotelBookingAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle hotel bookings."""
    location: str = Field(
        description="The location where the user wants to book a hotel."
    )
    checkin_date: str = Field(description="The check-in date for the hotel.")
    checkout_date: str = Field(description="The check-out date for the hotel.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the hotel booking."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Zurich",
                "checkin_date": "2023-08-15",
                "checkout_date": "2023-08-20",
                "request": "I prefer a hotel near the city center with a room that has a view."
            }
        }

class ToBookExcursion(BaseModel):
    """Transfers work to a specialized assistant to handle trip recommendation and other excursion bookings."""
    location: str = Field(
        description="The location where the user wants to book a recommended trip."
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the trip recommendation."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Lucerne",
                "request": "The user is interested in outdoor activities and scenic views."
            }
        }
