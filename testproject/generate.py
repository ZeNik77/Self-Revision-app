import requests
import json
import random
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django.core.files.storage import FileSystemStorage
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from .settings import MEDIA_ROOT
from .models import CourseChatHistory, Topic, Courses
from .KEYS import EMBED_TOKEN, API_KEY_IONET, EMBED_TOKEN_RESERVE, API_KEY_ANDREI
from django.core.cache import cache
import openai
import fitz
import os

# embeddings = OpenAIEmbeddings(
#     model="text-embedding-3-large",
#     openai_api_key=API_KEY_ANDREI,
#     openai_api_base="https://api.proxyapi.ru/openai/v1"
# )

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-mpnet-base-v2",
    task="feature-extraction",
    huggingfacehub_api_token=EMBED_TOKEN,
)

def remove_images(input_pdf):
    doc = fitz.open(fullPath(input_pdf))

    for page in doc:
        img_list = page.get_images(full=True)
        for img in img_list:
            xref = img[0]
            page.delete_image(xref)

    temp_output = input_pdf + ".temp"
    doc.save(fullPath(temp_output), garbage=4, deflate=True)
    doc.close()

    import gc
    gc.collect()
    import time
    time.sleep(0.1)

    os.replace(fullPath(temp_output), fullPath(input_pdf))

    fs = FileSystemStorage()
    fs.delete(temp_output)

    return input_pdf
def fullPath(path):
    return os.path.join(MEDIA_ROOT, path)

def load_and_chunk_documents(og_file_path, delete=False):
    if og_file_path:
        if og_file_path.endswith('.pdf'):
            remove_images(og_file_path)
            loader = PyPDFLoader(fullPath(og_file_path))
        else:  # txt, md, etc.
            loader = TextLoader(fullPath(og_file_path))
        
        pages = loader.load()
        if delete:
            fs = FileSystemStorage()
            fs.delete(og_file_path)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )
        return text_splitter.split_documents(pages)
    else:
        print('WARNING: load_chunk_documents() returns None')
        return None
# --- Vector Store Management ---
def create_vector_store(chunks, save_path):
    save_path = os.path.join(save_path, 'faiss_index')
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(save_path)
    return vector_store


def create_or_unify_vector_store(chunks, save_path):
    save_path = os.path.join(save_path, 'faiss_index')
    if chunks:
        vector_store = FAISS.from_documents(chunks, embeddings)
    if os.path.exists(save_path):
        unified = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
        if chunks:
            unified.merge_from(vector_store)
        return unified
    elif chunks:
        vector_store.save_local(save_path)
        return vector_store
    else:
        print('create_or_unify_vector_store() went to shit')
def generate_with_rag(history, path, course_id=-1, topic_id=-1, unified=False, delete=False, save=True, strict=True):
    chunks = load_and_chunk_documents(path, delete)
    if topic_id != -1:
        faiss_path = f'topic_faiss/{topic_id}'
    elif course_id != -1:
        faiss_path = f'course_faiss/{course_id}'
    else:
        print('Provide either topic_id or course_id')
        return None
    if unified:
        vector_store = create_or_unify_vector_store(chunks, faiss_path)
    else:
        vector_store = create_vector_store(chunks, faiss_path)
    # Extract last user question
    last_message = [m for m in history if m['role'] == 'user'][-1]
    query = last_message['content']
    
    # Retrieve relevant context
    
    docs_and_scores = vector_store.similarity_search_with_score(query, k=3)

    docs = [doc for doc, score in docs_and_scores if score >= 1.2]
    
    # docs = vector_store.similarity_search(query, k=3)

    context = "\n".join([doc.page_content for doc in docs])
    # print(context)
    # Augment the prompt
    rag_prompt_strict = {
        "role": "system",
        "content": f"""Answer ONLY using the context below. If you don’t find enough information, reply EXACTLY: 'FOUND NOTHING' (without the quotations). Do NOT add any extra knowledge.

        
        Context:
        {context}
        
        Current conversation:"""
    }
    rag_prompt_nonStrict1 = {
        "role": "system",
        "content": f"""You are a helpful study assistant. Use the context below as your **main source of truth**. You may rely on your general knowledge to clarify or expand on the content when necessary, but you must clearly base your answer on the provided context whenever possible.

        If the context does not cover the question at all, reply EXACTLY with: 'FOUND NOTHING' (without quotes).

        Context:
        {context}

        Current conversation:"""
    }
    rag_prompt_nonStrict2 = {
    "role": "system",
    "content": f"""You are a helpful study assistant.
    Use the context below as your **main source of truth**. You may rely on your general knowledge to clarify or expand when necessary, but you must base your answer on the provided context whenever possible.

    In your reply:
    - **Do not** include any reasoning, analysis, or commentary about what you are doing or how you are interpreting the context.
    - **Do not** describe which parts of the context you used.
    - **Do not** mention this prompt or the instructions.
    - If the context does not cover the question at all, reply EXACTLY with: FOUND NOTHING (without quotes).

    Provide **only** the final answer to the user’s question, formatted cleanly and directly.

    Context:
    {context}

    Current conversation:"""
    }

    if strict:
        rag_prompt = rag_prompt_strict
    else:
        rag_prompt = rag_prompt_nonStrict2

    augmented_history = [rag_prompt] + history
    res = generate(augmented_history)
    if not save:
        augmented_history = history
    return (augmented_history, res)


def generate(history):
    API_URL_IONET = 'https://api.intelligence.io.solutions/api/v1/'
    MODEL_IONET = 'deepseek-ai/DeepSeek-R1-0528'

    API_URL_PROXYAPI = 'https://api.proxyapi.ru/deepseek'
    MODEL_PROXYAPI = 'deepseek-chat'

    # API_KEY = API_KEY_ANDREI
    # API_URL = API_URL_PROXYAPI
    # MODEL = MODEL_PROXYAPI


    API_KEY = API_KEY_IONET
    API_URL = API_URL_IONET
    MODEL = MODEL_IONET


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
    # return response.choices[0].message.content

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

def deepSeek(input, course, course_id, topic_name, topic_description):
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
    # print('here-1')
    # try:
    att = 1
    cache.set('divideIntoSubtopicsStatusOld', '')
    cache.set('divideIntoSubtopicsStatus', f'Dividing into subtopics. Attempt {att}.')
    hist, x = generate_with_rag([{'role': 'user', 'content': content}], path, course_id=course_id, delete=True)
    print('\n\n\n', cache.get('divideIntoSubtopicsStatus'), '\n\n\n')
    while 'FOUND NOTHING' in x:
        att += 1
        if att > 5:
            return
        cache.set('divideIntoSubtopicsStatus', f'Dividing into subtopics. Attempt {att}.')
        print(cache.get('divideIntoSubtopicsStatus'))
        hist, x = generate_with_rag([{'role': 'user', 'content': content}], '', course_id=course_id, unified=True)
    x = x.replace('\n', '')
    print('topics found', x)
    topics = json.loads(x)
    # except Exception as e:
    #     print('=====\n', x, '\n=====')
    #     print('=====\n', e, '\n=====')
    #     # topics = []
    #     raise e
    print('json parsed')
    if topics:
        for topic in topics:
            name = topic.capitalize()
            cache.set('divideIntoSubtopicsStatus', f'Processing topics: "{name}"')
            print(cache.get('divideIntoSubtopicsStatus'))
            course = Courses.objects.get(course_id=course_id).name
            # content2 = f"Summarize the following information about the topic \"{name}\" into a clear, structured summary using bullet points. Focus only on what’s in the supplied material. Do NOT add any extra content or assumptions."
            content2 = f"""You are a study assistant. Generate a clear, structured summary in English about the topic "{name}" from the course "{course}".

Your summary must:
- Include both obvious and subtle or often overlooked details.
- Highlight important terms using <b>bold</b> or <i>italic</i> HTML tags.
- If your answer contains any mathematical expressions—whether they are full equations or single symbols like "\\nabla f"—wrap them exactly in the following block format:
  <div class="latex">YOUR_LATEX_HERE</div>
- Place LaTeX blocks on their **own line** immediately after the sentence they relate to. Do not inline LaTeX with normal text.
- Do not use any other tags, styles, or wrappers for LaTeX.

Write only the formatted summary without any introductions, conclusions, or extra explanations.
"""
            hist = [{"role": "user", "content": content2}]
            description = (generate_with_rag(hist, '', course_id=course_id, unified=True, strict=False))[1]
            if 'FOUND NOTHING' in description:
                print(f'Found nothing on topic "{name}"')
                continue
            topic_id = random.randint(2, 2147483646)
            while Topic.objects.filter(topic_id=topic_id).exists():
                topic_id = random.randint(2, 2147483646)
            Topic.objects.create(user_id=user_id, course_id=course_id, topic_id=topic_id, name=name, description=description, revision='')