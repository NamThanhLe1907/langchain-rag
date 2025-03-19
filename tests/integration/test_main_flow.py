import unicodedata
import uuid
from dotenv import load_dotenv
from core.assistants.graphs import part_4_graph
from core.assistants.prompts import (
                            update_flight_runnable,
                            book_car_rental_runnable,
                            book_hotel_runnable,
                            book_excursion_runnable,
                            assistant_runnable,
                            update_flight_tools,
                            book_hotel_tools,
                            book_car_rental_tools,
                            book_excursion_tools,
                            fetch_user_flight_information
)
from infrastructure.database import update_dates, db
from integrations.tools.utils import _print_event
from langsmith import Client
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
import sys, os
# print("Python Path:", sys.path)
# print("Current Working Directory:", os.getcwd())
# print("Directory Contents:", os.listdir(os.getcwd()))
# ✅ Load biến môi trường
load_dotenv()
class AIAgentGraph:
    def __init__(self):
        """✅ Khởi tạo Agent với thread_id và passenger_id từ input người dùng."""
        update_dates(db)
    def get_passenger_id(self):
        """✅ Hỏi người dùng nhập Passenger ID."""
        raw_input = input("\n🚀 **Nhập Passenger ID của bạn (hoặc '1' để dùng mặc định):** ").strip()
        
        if raw_input == "1":
            passenger_id = "3442 587242"
            return self.clean_text(passenger_id)  # ✅ Đúng thụt lề

        if raw_input:
            return self.clean_text(raw_input)  # ✅ Chuẩn hóa cả input của người dùng
        
        print("❌ Passenger ID không được để trống!")

    @staticmethod
    def clean_text(text):
        """✅ Chuẩn hóa text để tránh lỗi Unicode."""
        if not isinstance(text, str):
            text = str(text)
        return unicodedata.normalize('NFKC', text).encode('utf-8', 'replace').decode('utf-8')

    def get_user_input(self):
        """✅ Nhận câu hỏi từ User."""
        return self.clean_text(input("\n🧑 **USER :** ")).strip()

    def run(self):
        """✅ Chạy hội thoại với LangGraph."""
        print("\n🎤 **BẮT ĐẦU HỘI THOẠI VỚI TRỢ LÝ. GÕ 'exit' ĐỂ THOÁT.**\n")
        
        # ✅ Nhập Passenger ID và tạo Thread ID
        self.passenger_id = self.get_passenger_id()
        self.thread_id = str(uuid.uuid4())

        # ✅ Cấu hình lại `config`
        self.config = {
            "configurable": {
                "thread_id": self.thread_id,
                "passenger_id": self.passenger_id,
            }
        }

        # ✅ Danh sách câu hỏi giả lập
        tutorial_questions = [
            "Hi there, what time is my flight?",
            "Am I allowed to update my flight to something sooner? I want to leave later today.",
            "Update my flight to sometime next week then",
            "The next available option is great",
            "What about lodging and transportation?",
            "Yeah, I think I'd like an affordable hotel for my week-long stay (7 days). And I'll want to rent a car.",
            "OK, could you place a reservation for your recommended hotel? It sounds nice.",
            "Yes, go ahead and book anything that's moderate expense and has availability.",
            "Now for a car, what are my options?",
            "Awesome, let's just get the cheapest option. Go ahead and book for 7 days.",
            "Cool, so now what recommendations do you have on excursions?",
            "Are they available while I'm there?",
            "Interesting - I like the museums, what options are there?",
            "OK, great pick one and book it for my second day there.",
        ]

        _printed = set()

        for question in tutorial_questions:
            try:
                # ✅ Bắt đầu hội thoại
                print(f"\n🧑 **USER :** {question}")

                events = part_4_graph.stream({"messages": ("user", question)}, self.config, stream_mode="values")

                for event in events:
                    _print_event(event, _printed)

                # ✅ Xử lý tool calls
                while True:
                    snapshot = part_4_graph.get_state(config=self.config)

                    if not snapshot.next:
                        break

                    print("\n🔍 **DEBUG: AI ĐANG CHỜ TOOL PHẢN HỒI...**")

                    # ✅ Lấy tool call info từ message GỐC
                    original_ai_message = next(
                        msg for msg in reversed(snapshot.values["messages"])
                        if isinstance(msg, AIMessage) and msg.tool_calls
                    )

                    for tool_call in original_ai_message.tool_calls:
                        tool_call_id = tool_call["id"]
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]

                        print(f"\n🔧 **AI YÊU CẦU TOOL: {tool_name} ({tool_call_id})**")
                        print(f"📝 **Arguments:** {tool_args}")

                        # ✅ Tự động chấp nhận tool (không cần nhập "y")
                        print(f"\n✅ **Tự động thực thi tool {tool_name}...**")

                        # ✅ Chọn assistant phù hợp
                        if tool_name in [t.name for t in update_flight_tools]:
                            assistant = update_flight_runnable
                        elif tool_name in [t.name for t in book_hotel_tools]:
                            assistant = book_hotel_runnable
                        elif tool_name in [t.name for t in book_car_rental_tools]:
                            assistant = book_car_rental_runnable
                        elif tool_name in [t.name for t in book_excursion_tools]:
                            assistant = book_excursion_runnable
                        else:
                            assistant = assistant_runnable  # Mặc định: dùng assistant chính

                        # ✅ Kiểm tra và chuẩn hóa dữ liệu đầu vào
                        messages = snapshot.values.get("messages", [])
                        if not isinstance(messages, list):
                            messages = [messages]

                        user_info = fetch_user_flight_information.invoke(
                            {"configurable": {"passenger_id": self.passenger_id}}
                        ) or {}

                        if not isinstance(user_info, dict):
                            print(f"❌ Lỗi: user_info không phải dict! user_info={user_info}")
                            user_info = {}

                        if not isinstance(tool_args, dict):
                            print(f"❌ Tool error: tool_args không hợp lệ! tool_args={tool_args}")
                            tool_response = "❌ Tool error: Invalid tool arguments."
                        else:
                            try:
                                tool_result = assistant.invoke(
                                    {"messages": messages, "user_info": user_info},
                                    config={"configurable": {"passenger_id": self.passenger_id}},
                                )
                                tool_response = f"✅ {tool_name} result: {tool_result}"
                            except Exception as e:
                                tool_response = f"❌ Tool error: {str(e)}"

                        # ✅ Gửi phản hồi tool vào graph
                        tool_message = ToolMessage(
                            tool_call_id=tool_call_id,
                            content=tool_response
                        )

                        new_events = part_4_graph.stream(
                            {"messages": [tool_message]},
                            config=self.config,
                            stream_mode="values"
                        )

                        for event in new_events:
                            _print_event(event, _printed)

                    snapshot = part_4_graph.get_state(config=self.config)

            except Exception as e:
                print(f"\n⚠️ **Lỗi khi chạy graph:** {e}")


if __name__ == "__main__":
    agent = AIAgentGraph()
    agent.run()
