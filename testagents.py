import json
import os
from dotenv import load_dotenv
load_dotenv()  # Tải biến môi trường từ file .env

from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
# Bộ nhớ hội thoại
from langchain.memory import ConversationBufferMemory

import unicodedata

class AIAgentFAQ:
    """
    Lớp AIAgent quản lý toàn bộ quy trình RAG và hỗ trợ hội thoại đa lượt:
    - Load FAQ Data từ file JSON
    - Chuyển dữ liệu thành Document
    - Tạo embeddings và xây dựng vector store với FAISS
    - Tạo retriever từ vector store
    - Khởi tạo LLM và xây dựng ConversationalRetrievalChain để sinh câu trả lời
      và lưu giữ lịch sử hội thoại
    """

    def __init__(self, faq_file_path, model_name_llm="google/gemini-2.0-pro-exp-02-05:free", llm_temperature=0.7, k=2):
        """
        Khởi tạo AIAgent với các tham số:
        - faq_file_path: Đường dẫn tới file JSON chứa FAQ
        - model_name_llm: Tên của mô hình LLM (ChatOpenAI) dùng để sinh câu trả lời
        - llm_temperature: Tham số temperature của LLM (điều chỉnh độ sáng tạo của phản hồi)
        - k: Số lượng tài liệu liên quan cần truy xuất (trong vector search)
        """
        self.faq_file_path = faq_file_path   # Đường dẫn đến dữ liệu FAQ
        self.documents = []                   # Danh sách Document chứa FAQ
        self.embeddings = None                # Đối tượng embeddings (chuyển văn bản thành vector)
        self.vectorstore = None               # FAISS vector store chứa vector embeddings
        self.retriever = None                 # Retriever dùng để tìm các Document có nội dung tương tự
        self.llm = None                       # LLM (ChatOpenAI) dùng để sinh phản hồi
        self.chain = None                     # ConversationalRetrievalChain kết hợp retriever, LLM và bộ nhớ
        self.memory = None                    # Bộ nhớ hội thoại (conversation memory)
        self.k = k
        self.model_name_llm = model_name_llm
        self.llm_temperature = llm_temperature
        
        self.initialize_agent()

    def initialize_agent(self):
        """Khởi tạo toàn bộ thành phần của hệ thống."""
        self.load_faq_data()
        self.build_vectorstore()
        self.build_conversational_chain()

    def clean_text(self, text):
        """
        Làm sạch và chuẩn hóa chuỗi văn bản để loại bỏ các ký tự không hợp lệ.
        Sử dụng chuẩn hóa Unicode NFC và encoding với 'replace'.
        """
        if not isinstance(text, str):
            text = str(text)
        return unicodedata.normalize('NFC', text.encode('utf-8', 'replace').decode('utf-8'))

    def load_faq_data(self):
        """Load dữ liệu FAQ từ file JSON và chuyển đổi mỗi mục thành Document."""
        with open(self.faq_file_path, 'r', encoding='utf-8', errors='replace') as f:
            faq_data = json.load(f)
        for entry in faq_data:
            # Làm sạch nội dung nếu cần
            content = self.clean_text(f"Question: {entry['question']}\nAnswer: {entry['answer']}")
            self.documents.append(Document(page_content=content))
        print(f"Đã tải {len(self.documents)} tài liệu.")

    def build_vectorstore(self):
        """Tạo embeddings và vector store từ các Document đã load."""
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                                model_kwargs = {'device': 'cpu'},
                                                encode_kwargs = {'normalize_embeddings': False} 
                                                )
        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": self.k})

    def build_conversational_chain(self):
        """Khởi tạo LLM, bộ nhớ hội thoại và xây dựng ConversationalRetrievalChain."""
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",  # Endpoint của openrouter.ai
            model_name=self.model_name_llm,
            temperature=self.llm_temperature,
            # API key sẽ được lấy từ biến môi trường OPENAI_API_KEY
        )
        # Khởi tạo bộ nhớ hội thoại để lưu trữ lịch sử hội thoại
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        # Tạo ConversationalRetrievalChain để kết hợp LLM, retriever và memory
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            chain_type="stuff"
        )

    def answer_query(self, query):
        """
        Nhận truy vấn từ người dùng, làm sạch chuỗi và sử dụng ConversationalRetrievalChain để sinh câu trả lời.
        :param query: Truy vấn (string)
        :return: Câu trả lời (string)
        """
        # Làm sạch truy vấn để tránh lỗi encoding
        print("DEBUG: query type =", type(query))
        clean_query = self.clean_text(query)
        result = self.chain.invoke({"question": clean_query})
        return result["answer"]

    def start_conversation(self):
        """Phương thức tương tác liên tục với người dùng."""
        print("Chào mừng bạn đến với AI Agent. Gõ 'exit' để thoát.")
        while True:
            query = input("Bạn: ").strip().lower()
            if query in ["exit", "quit"]:
                print("Tạm biệt!")
                break
            answer = self.answer_query(query)
            print("Agent:", answer)

# Ví dụ sử dụng lớp AIAgentFAQ với hội thoại liên tục
if __name__ == "__main__":
    agent = AIAgentFAQ(faq_file_path="faq_data.json")
    agent.start_conversation()
