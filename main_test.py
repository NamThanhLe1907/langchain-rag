import json
import os
import unicodedata
import uuid
import shutil

from dotenv import load_dotenv
load_dotenv()  # Tải biến môi trường từ file .env

from langchain_core.messages import AIMessage, HumanMessage
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
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
    # Cập nhật DB (sử dụng hàm update_dates từ data/database.py)
        update_dates(db)  # Cập nhật DB theo file backup
        import uuid
        thread_id = str(uuid.uuid4())
        
        # Yêu cầu nhập Passenger ID ban đầu, làm sạch input
        passenger_id = ""
        while not passenger_id:
            passenger_id = self.clean_text(input("Nhập Passenger ID của bạn: ").strip())  #Available ID: "3442 587242"
            if not passenger_id:
                print("Passenger ID không được để trống. Vui lòng nhập lại!")
        
        config = {"configurable": {"thread_id": thread_id, "passenger_id": passenger_id}}
        
        # Khởi tạo state ban đầu cho graph: state chứa danh sách các message dưới dạng đối tượng (HumanMessage, AIMessage)
        initial_state: State = {"messages": []}
        print("Bắt đầu hội thoại theo graph (chế độ stream). Gõ 'exit' để thoát.")
        
        while True:
            query = self.clean_text(input("Bạn: ").strip())
            if query.lower() in ["exit", "quit"]:
                print("Tạm biệt!")
                break
            
            # Nếu người dùng muốn cập nhật passenger id, ví dụ: "update passenger id: 12345"
            if query.lower().startswith("update passenger id:"):
                new_id = self.clean_text(query.split(":", 1)[1].strip())
                if new_id:
                    config["configurable"]["passenger_id"] = new_id
                    print(f"Passenger ID đã được cập nhật thành: {new_id}")
                else:
                    print("Không nhận được giá trị passenger id mới. Vui lòng thử lại.")
                continue  # Bỏ qua phần xử lý query hiện tại
            
            # Thêm message của người dùng vào state
            initial_state["messages"].append(HumanMessage(content=query))
            
            # Sử dụng stream để in ra các event (cho debug)
            _printed = set()
            try:
                events = part_1_graph.stream(initial_state, config=config, stream_mode="values")
                for event in events:
                    _print_event(event, _printed)
            except Exception as e:
                print("Lỗi khi stream event:", e)
            
            # Gọi graph với state và config để lấy state mới
            try:
                new_state = part_1_graph.invoke(initial_state, config=config)
            except Exception as e:
                print("Lỗi khi invoke graph:", e)
                break
            
            # In ra phản hồi của assistant từ state mới
            if new_state["messages"]:
                last_msg = new_state["messages"][-1]
                try:
                    print("Agent (Graph):", last_msg.content)
                except AttributeError:
                    print("Agent (Graph):", last_msg)
            else:
                print("Agent (Graph): Không có phản hồi.")
            
            # Cập nhật state cho lượt tiếp theo
            initial_state = new_state


        
if __name__ == "__main__":
    agent = AIAgentFAQ()
    agent.start_graph_conversation()
