import requests
import json
import random
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django.core.files.storage import FileSystemStorage
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from .settings import MEDIA_ROOT
from .models import CourseChatHistory, Topic, Courses
import openai
import fitz

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
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")

def remove_images(input_pdf):
    # Load PDF
    doc = fitz.open(input_pdf)

    # Delete all images on all pages
    for page in doc:
        img_list = page.get_images(full=True)
        for img in img_list:
            xref = img[0]
            page.delete_image(xref)

    # Create a new file name
    base, ext = os.path.splitext(input_pdf)
    output_pdf = f"{base}_no_images{ext}"

    # Save cleaned PDF (compress and remove unused objects)
    doc.save(output_pdf, garbage=4, deflate=True)

    # Return new file path
    return output_pdf

def load_and_chunk_documents(og_file_path, delete=False):
    file_path = os.path.join(MEDIA_ROOT, og_file_path)
    deleted = False
    if file_path.endswith('.pdf'):
        # file_path = remove_images(file_path)
        # fs = FileSystemStorage()
        # fs.delete(og_file_path)
        loader = PyPDFLoader(file_path)
        # deleted = True
    else:  # txt, md, etc.
        loader = TextLoader(file_path)
    
    pages = loader.load()
    if delete and not deleted:
        fs = FileSystemStorage()
        fs.delete(og_file_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    return text_splitter.split_documents(pages)

# --- Vector Store Management ---
def create_or_load_vector_store(chunks, save_path="faiss_index"):
    # if os.path.exists(save_path):
    #     return FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
    # else:
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(save_path)
    return vector_store


def generate_with_rag(history, path, delete=False):
    chunks = load_and_chunk_documents(path, delete)
    vector_store = create_or_load_vector_store(chunks)
    # Extract last user question
    last_message = [m for m in history if m['role'] == 'user'][-1]
    query = last_message['content']
    
    # Retrieve relevant context
    
    docs_and_scores = vector_store.similarity_search_with_score(query, k=15)
    # docs = [doc for doc, score in docs_and_scores if score >= threshold]
    docs = [doc for doc, score in docs_and_scores if score >= 1.2]
    
    # docs = vector_store.similarity_search(query, k=3)

    context = "\n".join([doc.page_content for doc in docs])
    # Augment the prompt
    rag_prompt = {
        "role": "system",
        "content": f"""Answer ONLY using the context below. If you don’t find enough information, reply: 'I don't know.' Do NOT add any extra knowledge.

        
        Context:
        {context}
        
        Current conversation:"""
    }
    augmented_history = [rag_prompt] + history
    return (augmented_history, generate(augmented_history))


def generate(history):
    # API_KEY = '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'
    # API_URL = 'https://openrouter.ai/api/v1/chat/completions'
    # MODEL = "deepseek/deepseek-chat:free"
    
    
    # API_KEY = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjliMTVlODBmLWY3ODUtNDEzYy1hZjhiLTE5NDU4ODI5MTY4NSIsImV4cCI6NDkwNDUzOTE2N30.Xo4MbPTYxcjEq1TMwNQ_YTrGalMEn7U4oDOiadVsSnJbZiK_pRvh4pBU6UH8qr9uaVOKc1ryW6Yc--7ih0Ec6Q'


    API_KEY = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6ImJlMjgxY2IzLTgzYmYtNDIzMS1iNWQ1LTVlY2ZkNzcwNGY3ZiIsImV4cCI6NDkwNTY4MjAwNn0.Unm6RnQCdjytgIlyzXA8f1hyp0VN7ynCh6pBNwnkJNpeFT5BlZB6vEv375PBRT4ZggnVcvR2sADwPmn46lTSKw'
    API_URL = 'https://api.intelligence.io.solutions/api/v1/'
    MODEL = 'deepseek-ai/DeepSeek-R1-0528'

    # headers = {
    #     'Authorization': f'Bearer {API_KEY}',
    #     'Content-Type': 'application/json'
    # }

    # data = {
    #     "model": MODEL,
    #     'messages': history,
    #     'temperature': 1
    # }

    # response = requests.post(API_URL, headers=headers, json=data)
    # if 'error' in response.json() or not response.json().get('choices'):
    #     print('=======================\n', response.json()['error'], '\n=======================')
    #     return 'AI API error. Please, try again.'
    # # return response.json()["choices"][0]["message"]["content"]
    # return response.json()["choices"][0]["message"]["content"].split('</think>\n')[1]

    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=API_URL,
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=history,
        temperature=0.7,
        stream=False,
        # max_completion_tokens=50
    )
    return response.choices[0].message.content.split('</think>\n')[1]

def revise(course, topic_name, topic_description):
    content = f"""You are a study assistant. Generate a clear, structured summary in English on the topic "{topic_name}" from the course "{course}", using the following description as your reference:

{topic_description}

Your summary must:
- Always be formatted as a list of points, each starting with “-” and ending with “<br>”.
- Include both obvious and subtle or often overlooked points.
- Highlight important terms using <b>bold</b> or <i>italic</i> HTML tags.
- If your answer contains any mathematical expressions—whether they are full equations or single symbols like "\\nabla f"—**wrap them exactly** in the following block format:
  <div class="latex">YOUR_LATEX_HERE</div>
- Place LaTeX blocks on their **own line** right after the sentence they relate to. Do not inline LaTeX with normal text.
- Do not use any other tags, styles, or wrappers for LaTeX.
Do not include any greetings, introductions, or explanations—return only the summary.
"""
    answer = generate([{'role': 'user', 'content': content}])
    return answer

def deepSeek(input, course, course_id, topic_name, topic_description, internet_toggle, file_path):
    content = f"""You are a study assistant. Answer the user's question strictly on the topic "{topic_name}" from the course "{course}", using the following summary as your reference:

{topic_description}

Your response must follow these rules:
- Begin the response **exactly** with: "Answer: " (without quotes).
- Use <b>bold</b> and <i>italic</i> HTML tags to emphasize key terms.
- If your answer contains any mathematical expressions—whether they are full equations or single symbols like "\\nabla f"—**wrap them exactly** in the following block format:
  <div class="latex">YOUR_LATEX_HERE</div>
- Place LaTeX blocks on their **own line** right after the sentence they relate to. Do not inline LaTeX with normal text.
- Do not use any other tags, styles, or wrappers for LaTeX.
- If the question is unrelated to the topic, respond with only: "The question is not related to the specified topic."

Do not include any greetings, introductions, or explanations—return only the direct answer.

Here is the question: {input}
"""
    try:
        history = CourseChatHistory.objects.get(course_id=course_id)
    except:
        history = CourseChatHistory.objects.create(course_id=course_id, history=[])
    history.history.append({"role": "user", 'message': input, "content": content})
    history.save() 
    if file_path:
        new_history, answer = generate_with_rag(history.history, file_path, delete=True)
        history.history = new_history
    else:
        answer = generate(history.history)
    history.history.append({'role': 'assistant', 'content': answer})
    history.save()
    return answer

def generateTest(topic_name, topic_description):
    jsonString = '[{"question": "Question text", "answer": ["Correct answer", "Wrong answer 1", "Wrong answer 2"]}, ...]'
    content = "Generate a 5 single-choice questions test on the topic \""+topic_name+"\" with the content \""+topic_description+"\". Format your answer strictly as a valid JSON array in a single line, like this: "+jsonString+". Do not add any commentary, preamble, or explanation. Your response must be a single JSON string without any line breaks or \ escape characters. The first answer in each array must be the correct one."
    
    generated = generate([{"role": "user", "content": content}])
    test = json.loads(generated)
    correct = []
    for i in range(len(test)):
        q = test[i]
        question = q['question']
        answer = q['answer']
        correct.append(answer[0])
        random.shuffle(answer)
        test[i] = {'number': i+1, 'question': question, 'answer': answer}
    return (test, correct)


def divideToSubtopics(path, course_id, user_id):
    content = '''You are an expert educational content analyst. From the course content provided below, extract a comprehensive flat list of concrete, specific topics, subtopics, and named concepts. 

Guidelines:
- Focus on the **major parts of the course** (for example, "Limits," "Derivatives," "Integrals," "Multivariable Calculus").
- Within each major part, identify all the **key specific subtopics or techniques**, such as "Taylor series," "Jacobian determinant," or "gradient."
- Use clear, canonical names that are used in textbooks. Avoid vague formulations like "functions from ℝ² to ℝ⁴" or "differential of a multi-dimensional function."
- Do **not** produce general or umbrella labels like "Calculus," "Analysis," "Linear Algebra."
- Do **not** produce nested groupings or explanations—only a flat list of concrete subtopics.
- Be comprehensive. Err on the side of **including more topics** rather than too few.
- Format the output as a single-line JSON array of strings, each string being a single subtopic.

**Here is the course content:**
'''
    topics = []
    print('here-1')
    try:
        hist, x = generate_with_rag([{'role': 'user', 'content': content}], path)
        print('here', x)
        topics = json.loads(x)
    except Exception as e:
        print('=====\n', x, '\n=====')
        print('=====\n', e, '\n=====')
        topics = []
    print('here2')
    print(x)
    if topics:
        for topic in topics:
            topic_id = random.randint(2, 2147483646)
            while Topic.objects.filter(topic_id=topic_id).exists():
                topic_id = random.randint(2, 2147483646)
            name = topic.capitalize()
            course = Courses.objects.get(course_id=course_id).name
            # content2 = f"Summarize the following information about the topic \"{name}\" into a clear, structured summary using bullet points. Focus only on what’s in the supplied material. Do NOT add any extra content or assumptions."
            content2 = f"""You are a study assistant. Generate a clear, structured summary in English about the topic "{name}" from the course "{course}".

Your summary must:
- Always be formatted as a list of points, each starting with “-” and ending with “<br>”.
- Include both obvious and subtle or often overlooked details.
- Highlight important terms using <b>bold</b> or <i>italic</i> HTML tags.
- If your answer contains any mathematical expressions—whether they are full equations or single symbols like "\\nabla f"—wrap them exactly in the following block format:
  <div class="latex">YOUR_LATEX_HERE</div>
- Place LaTeX blocks on their **own line** immediately after the sentence they relate to. Do not inline LaTeX with normal text.
- Do not use any other tags, styles, or wrappers for LaTeX.

Write only the formatted summary without any introductions, conclusions, or extra explanations.
"""
            hist = [{"role": "user", "content": content2}]
            description = (generate_with_rag(hist, path))[1]
            Topic.objects.create(user_id=user_id, course_id=course_id, topic_id=topic_id, name=name, description=description, revisions=[])
#TODO: Remove pictures from pdf files.
#TODO: Replace "I don't know"s with nothing
#TODO: Separate FAISS DBs