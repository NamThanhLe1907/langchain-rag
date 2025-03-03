import unicodedata
import uuid
import sys

from dotenv import load_dotenv
load_dotenv()  # Tải biến môi trường từ file .env
from langchain_core.messages import AIMessage, HumanMessage
# Import graph builder để có part_1_graph
from graph_builder import part_1_graph
from data.state import State
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
        
    #     self.initialize_agent()

    # def initialize_agent(self):
    #     self.load_faq_data()
    #     self.build_vectorstore()
    #     self.build_conversational_chain()

    # def load_faq_data(self):
    #     with open(self.faq_file_path, 'r', encoding='utf-8', errors='replace') as f:
    #         faq_data = json.load(f)
    #     for entry in faq_data:
    #         content = self.clean_text(f"Question: {entry['question']}\\nAnswer: {entry['answer']}")
    #         self.documents.append(Document(page_content=content))
    #     print(f"Đã tải {len(self.documents)} tài liệu.")

    # def build_vectorstore(self):
    #     self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
    #                                             model_kwargs={'device': 'cpu'},
    #                                             encode_kwargs={'normalize_embeddings': False})
    #     self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
    #     self.retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": self.k})

    # def build_conversational_chain(self):
    #     self.llm = ChatOpenAI(
    #         model_name=self.model_name_llm,
    #         temperature=self.llm_temperature,
    #     )
    #     # self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    #     # self.chain = ConversationalRetrievalChain.from_llm(
    #     #     llm=self.llm,
    #     #     retriever=self.retriever,
    #     #     memory=self.memory,
    #     #     chain_type="stuff"
    #     # )

    # def answer_query(self, query):
    #     clean_query = self.clean_text(query)
    #     result = self.chain.invoke({"question": clean_query})
    #     return result["answer"]

    # def start_conversation(self):
    #     print("Chào mừng bạn. Gõ 'exit' để thoát.")
    #     while True:
    #         query = input("Bạn: ").strip().lower()
    #         if query in ["exit", "quit"]:
    #             print("Tạm biệt!")
    #             break
    #         # Sử dụng chain đơn giản cho FAQ\n
    #         answer = self.answer_query(query)
    #         print("Agent (FAQ):", answer)

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
        passenger_id = ""   #Available ID: "3442 587242"
        while not passenger_id:
            try:
                raw_input = input("Nhập Passenger ID của bạn: ").strip()
                passenger_id = self.clean_text(raw_input)
                if not passenger_id:
                    print("❌ Passenger ID không được để trống. Vui lòng nhập lại!")
            except EOFError:
                print("\n⛔ Đã nhận tín hiệu EOF. Thoát chương trình.")
                sys.exit(0)

        config = {"configurable": {"thread_id": thread_id, "passenger_id": passenger_id}}
        
        # Khởi tạo state ban đầu
        initial_state = {"messages": []}
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

            # Thêm message của người dùng vào state
            initial_state["messages"].append(HumanMessage(content=query))

            # Debug: Kiểm tra messages trong state
            print(f"📩 DEBUG - State hiện tại: {initial_state['messages']}")

            # Stream events để debug
            _printed = set()
            try:
                events = part_1_graph.stream(initial_state, config=config, stream_mode="values")
                for event in events:
                    _print_event(event, _printed)
            except Exception as e:
                print(f"⚠️ Lỗi khi stream event: {e}")

            # Gọi graph với state để lấy state mới
            try:
                new_state = part_1_graph.invoke(initial_state, config=config)
            except Exception as e:
                print(f"⚠️ Lỗi khi invoke graph: {e}")
                break

            # In phản hồi từ assistant
            if new_state.get("messages"):
                last_msg = new_state["messages"][-1]
                print(f"🤖 Agent (Graph): {last_msg.content if isinstance(last_msg, AIMessage) else last_msg}")
            else:
                print("🤖 Agent (Graph): Không có phản hồi.")

            # Cập nhật state mới
            initial_state = new_state



        
if __name__ == "__main__":
    agent = AIAgentFAQ()
    agent.start_graph_conversation()
