import json
from langchain.docstore.document import Document
# Sử dụng HuggingFaceEmbeddings để tạo embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI


# --- Bước 1: Load dữ liệu FAQ từ file JSON ---
with open('faq_data.json', 'r', encoding='utf-8') as f:
    faq_data = json.load(f)

# --- Bước 2: Tạo danh sách Document từ dữ liệu ---
documents = []
for entry in faq_data:
    content = f"Question: {entry['question']}\nAnswer: {entry['answer']}"
    documents.append(Document(page_content=content))

print(f"Đã tải {len(documents)} tài liệu.")

# --- Bước 3: Tạo embeddings và vector store ---
# Sử dụng HuggingFaceEmbeddings thay vì OpenAIEmbeddings vì openrouter không hỗ trợ embedding endpoint
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(documents, embeddings)

# --- Bước 4: Tạo retriever từ vector store ---
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})

# --- Bước 5: Khởi tạo LLM với openrouter.ai ---
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",  # Endpoint của openrouter.ai
    model_name="google/gemini-2.0-pro-exp-02-05:free",
    temperature=0.7,
    # API key sẽ được lấy từ biến môi trường OPENAI_API_KEY nếu bạn đã export
)

# --- Bước 6: Xây dựng chain RetrievalQA ---
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

# --- Bước 7: Gửi truy vấn và nhận kết quả ---
query = "Làm thế nào để đăng ký dịch vụ?"
response = qa_chain.run(query)
print("Câu trả lời:", response)
