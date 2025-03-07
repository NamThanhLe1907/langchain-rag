import unicodedata
import uuid
import sys

from dotenv import load_dotenv
load_dotenv()  # Tải biến môi trường từ file .env
from langchain_core.messages import AIMessage, HumanMessage
# Import graph builder để có part_1_graph
from graph_builder import part_2_graph
from assistants import State
from data.database import update_dates, db
from tools.tool_util import _print_event

class AIAgentFAQ:
    def __init__(self, model_name_llm="gpt-4o-mini", llm_temperature=0.7, k=2):
        # self.faq_file_path = faq_file_path
        self.documents = []
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.chain = None
        self.memory = None
        self.k = k
        self.model_name_llm = model_name_llm
        self.llm_temperature = llm_temperature

    def clean_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        # Sử dụng NFKC để chuẩn hóa và encode với 'replace' để xử lý các ký tự không hợp lệ
        normalized = unicodedata.normalize('NFKC', text)
        return normalized.encode('utf-8', 'replace').decode('utf-8')


    def start_graph_conversation(self):
        """Chạy hội thoại với graph agent."""
        
        # Cập nhật DB theo file backup
        update_dates(db)

        # Tạo ID thread duy nhất
        thread_id = str(uuid.uuid4())

        # Yêu cầu nhập Passenger ID ban đầu
        passenger_id = None  # Available ID: "3442 587242"
        while not passenger_id:
            try:
                raw_input = input("Nhập Passenger ID của bạn: ").strip()
                if raw_input.lower() == "1":
                    passenger_id = "3442 587242"
                else:
                    passenger_id = self.clean_text(raw_input)
                    
                if not passenger_id:
                    print("❌ Passenger ID không được để trống. Vui lòng nhập lại!")
            except EOFError:
                print("\n⛔ Đã nhận tín hiệu EOF. Thoát chương trình.")
                sys.exit(0)

        config = {"configurable": {"thread_id": thread_id, "passenger_id": passenger_id}}

        print("🎤 Bắt đầu hội thoại theo graph (chế độ stream). Gõ 'exit' để thoát.")

        while True:
            try:
                raw_query = input("Bạn: ").strip()
            except EOFError:
                print("\n⛔ Đã nhận tín hiệu EOF. Thoát chương trình.")
                sys.exit(0)

            query = self.clean_text(raw_query)  # Làm sạch input

            # Kiểm tra nếu người dùng muốn thoát
            if query.lower() in ["exit", "quit"]:
                print("👋 Tạm biệt! Hẹn gặp lại.")
                sys.exit(0)

            # Nếu người dùng muốn cập nhật Passenger ID
            if query.lower().startswith("update passenger id:"):
                new_id = self.clean_text(query.split(":", 1)[1].strip())
                if new_id:
                    config["configurable"]["passenger_id"] = new_id
                    print(f"✅ Passenger ID đã cập nhật thành: {new_id}")
                else:
                    print("❌ Không nhận được Passenger ID mới. Vui lòng thử lại.")
                continue  # Bỏ qua xử lý query hiện tại

            # ✅ Lấy state hiện tại từ LangGraph
            state = part_2_graph.get_state(config)
            
            # ✅ Thêm message mới vào state
            state["messages"].append(HumanMessage(content=query))

            # Debug: Kiểm tra messages trong state
            print(f"📩 DEBUG - State hiện tại: {state['messages']}")

            # ✅ Gửi state vào graph để xử lý
            _printed = set()
            try:
                events = part_2_graph.stream(state, config=config, stream_mode="values")
                for event in events:
                    _print_event(event, _printed)
            except Exception as e:
                print(f"⚠️ Lỗi khi stream event: {e}")
            



        
if __name__ == "__main__":
    agent = AIAgentFAQ()
    agent.start_graph_conversation()
