import unicodedata
import uuid
from dotenv import load_dotenv
from graph_builder import part_2_tools, memory, builder
from data.database import update_dates, db
from tools.tool_util import _print_event
from langsmith import Client
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import merge_configs

# ✅ Load biến môi trường
load_dotenv()

class AIAgentGraph:
    def __init__(self):
        """✅ Khởi tạo Agent với thread_id và passenger_id từ input người dùng."""

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
        # ✅ Bây giờ mới yêu cầu nhập Passenger ID và tạo Thread ID
        self.passenger_id = self.get_passenger_id()
        self.thread_id = str(uuid.uuid4())

        # ✅ Cấu hình lại `config`
        self.config = {
            "configurable": {
                "thread_id": self.thread_id,
                "passenger_id": self.passenger_id,
            }
        }
        
        # ✅ Biên dịch lại `graph` với `config` mới
        part_2_graph = builder.compile(checkpointer=memory, interrupt_before=["tools"])


        tutorial_questions = [
                "Hi there, what time is my flight?",
                "Am i allowed to update my flight to something sooner? I want to leave later today.",
                "Update my flight to sometime next week then",
                "The next available option is great",
                "what about lodging and transportation?",
                "Yeah i think i'd like an affordable hotel for my week-long stay (7 days). And I'll want to rent a car.",
                "OK could you place a reservation for your recommended hotel? It sounds nice.",
                "yes go ahead and book anything that's moderate expense and has availability.",
                "Now for a car, what are my options?",
                "Awesome let's just get the cheapest option. Go ahead and book for 7 days",
                "Cool so now what recommendations do you have on excursions?",
                "Are they available while I'm there?",
                "interesting - i like the museums, what options are there? ",
                "OK great pick one and book it for my second day there.",
            ]
        while True:
            try:
                
                # user_input = self.get_user_input()
                # if user_input.lower() == "exit":
                #     print("\n👋 **TẠM BIỆT!**\n")
                #     break
                
                # print(f"\n🧑 **USER :** {user_input}")
                _printed = set()
                
       #         snapshot2 = part_2_graph.get_state(config = self.config)
       #         print("DEBUG snapshot2\n",snapshot2.config)
                # ✅ Khởi tạo conversation
                # inputs = {"messages": [HumanMessage(content=user_input)]}
                for question in tutorial_questions:
                                                    
                    events = part_2_graph.stream({"messages": ("user", question)}, self.config, stream_mode="values")
    
        
                    for event in events:
                        _print_event(event, _printed)
                    # ✅ Xử lý tool calls
                    while True:
                        snapshot = part_2_graph.get_state(config = self.config)

               #         print("\n=== DEBUG: Trước khi merge config ===")
               #         print("self.config:", self.config)
               #         print("snapshot.config:", snapshot.config)
                        if not snapshot.next:
                            break
                          
                #        print("\n=== DEBUG: Sau khi merge config ===")
                #        print("merged_config:", merged_config)
                      
                        print("\n🔍 **DEBUG: AI ĐANG CHỜ TOOL PHẢN HỒI...**")
                        user_choice = input("\n⏳ **Bạn có đồng ý thực hiện tool này? (y/n):** ").strip().lower()
        
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
        
                            # ✅ Hỏi user có đồng ý chạy tool không
                            user_choice = input(f"\n⏳ **Bạn có đồng ý thực hiện tool {tool_name}? (y/n):** ").strip().lower()
                            if user_choice != "y":
                                print(f"\n❌ **User từ chối tool {tool_name}.**")
                                tool_response = f"User denied execution of {tool_name}."
                            else:
                                print(f"\n✅ **Đang thực thi tool {tool_name}...**")
                                try:
                                    tool = next(t for t in part_2_tools if t.name == tool_name)
                                    
                                    tool_args["passenger_id"] = self.passenger_id
                                    tool_result = tool.invoke(
                                                                  tool_args, 
                                                                  config={"configurable": {"passenger_id": self.passenger_id}}
                                                              )
                                    tool_response = f"✅ {tool_name} result: {tool_result}"
                                except Exception as e:
                                    tool_response = f"❌ Tool error: {str(e)}"
        
                            # ✅ Tạo tool message
                            tool_message = ToolMessage(
                                tool_call_id=tool_call_id,
                                content=tool_response
                            )
        
                            # ✅ Stream tool message vào graph để cập nhật state
                            new_events = part_2_graph.stream(
                                {"messages": [tool_message]},
                                config = self.config,
                                stream_mode="values"
                            )
                            # print("\n=== DEBUG: SAU khi gọi tool ===")
                            # print("snapshot.config:", snapshot.config)
                            # ✅ In phản hồi mới từ AI
                            for event in new_events:
                                _print_event(event, _printed)
        
                        snapshot = part_2_graph.get_state(config = self.config)
            except Exception as e:
                    print(f"\n⚠️ **Lỗi khi chạy graph:** {e}")

if __name__ == "__main__":
    agent = AIAgentGraph()
    agent.run()
