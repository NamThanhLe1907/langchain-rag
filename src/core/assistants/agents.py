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

# ✅ Hàm truy vấn database SQLite
def query_db(query: str, params: tuple = ()):
    """Truy vấn database SQLite và trả về kết quả."""
    conn = sqlite3.connect("travel2.sqlite")
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)  # Sử dụng parameterized query
        if query.strip().lower().startswith(("insert", "update", "delete")):
            conn.commit()  # Tự động commit cho các thao tác ghi
        results = cursor.fetchall()
        return results if results else []
    except sqlite3.Error as e:  # Bắt lỗi cụ thể từ SQLite
        conn.rollback()  # Rollback transaction nếu có lỗi
        raise RuntimeError(f"Lỗi truy vấn DB: {str(e)}") from e
    finally:
        conn.close()

# ✅ Định nghĩa State chung để dùng ở cả Assistant, Graph Builder, Main
class State(TypedDict):
    """✅ State chuẩn có đủ 'messages' và 'user_info'"""
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: dict | str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "update_flight",
                "book_car_rental",
                "book_hotel",
                "book_excursion",
            ]
        ],
        update_dialog_stack,
    ]

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


class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
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
                "request": "I need a compact car with automatic transmission.",
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
                "request": "I prefer a hotel near the city center with a room that has a view.",
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
                "request": "The user is interested in outdoor activities and scenic views.",
            }
        }
        



