import requests
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from .settings import MEDIA_ROOT


# url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {api_key}"
# }
# data = {
#     "model": "deepseek-ai/DeepSeek-R1",
#     "messages": [
#         {
#             "role": "user",
#             "content": content
#         }
#     ]
# }
# response.json()["choices"][0]["message"]["content"].split('</think>\n')[1]

# Initialize embedding model (local for cost efficiency)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def load_and_chunk_documents(file_path):
    file_path = os.path.join(MEDIA_ROOT, file_path)
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:  # txt, md, etc.
        loader = TextLoader(file_path)
        
    pages = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return text_splitter.split_documents(pages)

# --- Vector Store Management ---
def create_or_load_vector_store(chunks, save_path="faiss_index"):
    if os.path.exists(save_path):
        return FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
    else:
        vector_store = FAISS.from_documents(chunks, embeddings, allow_dangerous_deserialization=True)
        vector_store.save_local(save_path)
        return vector_store


def generate_with_rag(history, path):
    chunks = load_and_chunk_documents(path)
    vector_store = create_or_load_vector_store(chunks)
    # Extract last user question
    last_message = [m for m in history if m['role'] == 'user'][-1]
    query = last_message['content']
    
    # Retrieve relevant context
    docs = vector_store.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    # Augment the prompt
    rag_prompt = {
        "role": "system",
        "content": f"""Answer using ONLY the following context. If unsure, say you don't know.
        
        Context:
        {context}
        
        Current conversation:"""
    }
    augmented_history = [rag_prompt] + history
    return (augmented_history, generate(augmented_history))


def generate(history):
    API_KEY = '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'
    API_URL = 'https://openrouter.ai/api/v1/chat/completions'
    MODEL = "deepseek/deepseek-chat:free"

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": MODEL,
        'messages': history,
    }

    response = requests.post(API_URL, headers=headers, json=data)
    if 'error' in response.json():
        print('=======================\n', response.json()['error'], '\n=======================')
        return 'AI API error. Please, try again.'
    return response.json()["choices"][0]["message"]["content"]