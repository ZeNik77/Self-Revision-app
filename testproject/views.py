from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from openai import OpenAI
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm, LoginForm, AddCourseForm, AIForm, AddTopicForm, TestForm2
from .models import User, Courses, CourseChatHistory, Topic, Test
from .generate_tests import generateTest
from g4f.client import Client
from g4f.gui.server.internet import get_search_message
import requests
import random
import asyncio

def index(request):
    # processing POST request
    if request.method == 'POST':
        if 'login' in request.POST:
            login(request)
        elif 'register' in request.POST:
            signup(request)

    if not auth.get_user(request).is_active:
        return redirect(reverse('login'))
    else:  return redirect(reverse('home'))
def signup(request):
    if request.method == 'POST':
        signup_form = SignUpForm(data = request.POST)

        if signup_form.is_valid():

            # assigning an id for user
            if len(User.objects.all()) == 0:
                user_id = 1
            else:
                user_id = User.objects.all().last().user_id + 1

            # creatig new user
            user = signup_form.save()
            user.user_id = user_id
            user.save()

            # login into an account
            auth.login(request, user)
            
            return redirect(reverse('home'))
        
        # if we do not succeed with registration than return main page
        else:
            return render(request, 'signup.html', {'signup_form' : signup_form})
    return render(request, 'signup.html', {'signup_form': SignUpForm})

def login(request):
    if request.method == 'POST':

        login_form = LoginForm(data = request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user:
                auth.login(request, user)
                return redirect(reverse('home'))
            else:
                login_form.add_error(None, "No such user exists!")
                return render(request, 'login.html', {'login_form': login_form})
        else:
            return render(request, 'login.html', {'login_form': login_form})
    return render(request, 'login.html', {'login_form': LoginForm})

def logout(request):
    auth.logout(request)
    return redirect(reverse('index'))

def courses (request):
    if not auth.get_user(request).is_active:
        return redirect(reverse('index'))
    if request.method == "POST":
        if "add_course" in request.POST:
            form = AddCourseForm(data=request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                desc = form.cleaned_data['description']
                # if len(Courses.objects.all()) == 0:
                #     course_id = 0
                # else:
                #     course_id = Courses.objects.all().last().course_id + 1
                course_id = random.randint(2, 2147483646)
                while Courses.objects.filter(course_id=course_id).exists():
                    course_id = random.randint(2, 2147483646)
                Courses.objects.create(name=name, description=desc, user_id=auth.get_user(request).user_id, course_id=course_id)
            else:
                print(form.errors)
        if 'edit_course' in request.POST:
            course_id = request.POST['edit_course']
            new_name = request.POST['name']
            new_desc = request.POST['description']
            courses = Courses.objects.filter(id=course_id)
            if courses:
                courses[0].name = new_name
                courses[0].description = new_desc
                courses[0].save()
        elif 'delete_course' in request.POST:
            course_id = request.POST['delete_course']
            courses = Courses.objects.filter(course_id=course_id)
            topics = Topic.objects.filter(course_id=course_id)
            history = CourseChatHistory.objects.filter(course_id=course_id)
            tests = Test.objects.filter(course_id=course_id)
            for el in topics:
                el.delete()
            for el in tests:
                el.delete()
            for el in history:
                el.delete()
            if courses:
                courses[0].delete()
    return render (request, "courses.html", { "courses": Courses.objects.filter(user_id=auth.get_user(request).user_id), "form": AddCourseForm})
def donat(request):
    return render(request, 'donat.html')
def delete_topic(topic_id):
    topic = Topic.objects.filter(topic_id=topic_id)
    tests = Test.objects.filter(topic_id=topic_id)
    for el in tests:
        el.delete()
    if topic:
        topic[0].delete()
def course(request, course_id):
    if request.method == 'POST':
        if 'add_topic' in request.POST:
            form = AddTopicForm(data=request.POST)
            if form.is_valid():
                name = form.cleaned_data['topic_name']
                description = form.cleaned_data['topic_description']
                topic_id = random.randint(2, 2147483646)
                while Topic.objects.filter(topic_id=topic_id).exists():
                    topic_id = random.randint(2, 2147483646)
                Topic.objects.create(topic_id=topic_id, course_id=course_id, user_id=auth.get_user(request).user_id, name=name, description=description)
                return redirect(reverse('course', args=[course_id]))
            else:
                print(form.errors)
        if 'delete_topic' in request.POST:
            topic_id = request.POST['delete_topic']
            delete_topic(topic_id)
            return redirect(reverse('course', args=[course_id]))
    if Courses.objects.filter(course_id=course_id).exists():
        course = Courses.objects.get(course_id=course_id)
    else:
        return redirect(reverse('courses'))
    topics = Topic.objects.filter(course_id=course_id)
    return render(request, 'course.html', {'form': AIForm, 'addTopicForm': AddTopicForm, 'course': course, 'topics': topics})


def topic(request, course_id, topic_id):
    testError = ''
    if not auth.get_user(request).is_active or not Courses.objects.filter(user_id=auth.get_user(request).user_id, course_id=course_id).exists() or not Topic.objects.filter(user_id=auth.get_user(request).user_id, topic_id=topic_id).exists():
        return redirect(reverse('courses'))
    else:
        course = Courses.objects.get(course_id=course_id)
        topic = Topic.objects.get(topic_id=topic_id)
    
    if request.method == 'POST':
        # TODO: restrict repeated form submission
        if 'submit_addTest' in request.POST:
            try:
                (test, correct) = generateTest(topic.name, topic.description)
                test_id = random.randint(2, 2147483646)
                while Test.objects.filter(test_id=test_id).exists():
                    test_id = random.randint(2, 2147483646)
                Test.objects.create(test_id=test_id, user_id=auth.get_user(request).user_id, course_id=course_id, topic_id=topic_id, questions=test, correct=correct, correctQuestions=[], incorrectQuestions=[])
                for el in Test.objects.filter(topic_id=topic_id, passed=False):
                    if el.test_id != test_id:
                        el.delete()
            except:
                testError = 'Error while generating the test. Please try again.'
        if 'submit_revision' in request.POST:
            course = Courses.objects.get(course_id=course_id)
            topic = Topic.objects.get(topic_id=topic_id)
            revision = revise(course.name, topic.name, topic.description)
            topic.revisions.append(revision)
            topic.save()
        if 'submit_test' in request.POST:
            test = Test.objects.filter(topic_id=topic_id)
            if test.exists():
                test = test.last()
                if test.passed: return redirect(reverse('topic', args=(course_id, topic_id)))
            else:
                return redirect(reverse('topic'), args=(course_id, topic_id))
            form = TestForm2(request.POST, questions=test.questions, correct=test.correct)
            if form.is_valid():
                grade = 0
                correctQ = []
                incorrectQ = []
                full = len(form.correct)
                for i in range(len(form.correct)):
                    answer = form.cleaned_data[f'question_{i}']
                    correct = form.correct[i]
                    if answer == correct:
                        correctQ.append({'question': form.fields[f'question_{i}'].label, 'answer': answer})
                        grade += 1
                    else:
                        incorrectQ.append({'question': form.fields[f'question_{i}'].label, 'answer': answer, 'correct': correct})
                test.grade = int((grade/full) * 100)
                test.correctQuestions = correctQ
                test.incorrectQuestions = incorrectQ
                test.passed = True
                test.save()
            else:
                print(form.errors)

        if 'delete_topic' in request.POST:
            t_id = request.POST['delete_topic']
            delete_topic(t_id)
            return redirect(reverse('topic', args=(course_id, topic_id)))
        if 'delete_revision' in request.POST:
            rev_i = int(request.POST['delete_revision'])
            topic.revisions.pop(rev_i)
            topic.save()
        if 'delete_test' in request.POST:
            test_id = request.POST['delete_test']
            if (test := Test.objects.filter(test_id=test_id)).exists():
                test.delete()
    topics = Topic.objects.filter(course_id=course_id)
    test = Test.objects.filter(topic_id=topic_id, passed=False)
    passed_tests = Test.objects.filter(topic_id=topic_id, passed=True)
    if not test.exists():
        test = None
        testForm = None
    else:
        test = test.last()
        testForm = TestForm2(questions=test.questions, correct=test.correct)
    revisions = topic.revisions
    return render(request, 'course.html', {'form': AIForm, 'addTopicForm': AddTopicForm, 'course': course, 'topics': topics, 'topic': topic, 'test': test, 'test_form': testForm, 'revisions': revisions, 'passed_tests': passed_tests, 'test_error': testError})
    
def home(request):
    if auth.get_user(request).is_active:
        return render(request, 'landing.html')
    else:
        return redirect(reverse('login'))

def about(request):
    return render(request, 'about.html')

def revise(course, topic_name, topic_description):
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
    # content = f"Generate a clear, structured summary in English on the topic \"{topic_name}\" from the course \"{course}\" with the following description: {topic_description}. The summary must include key ideas, important details, and subtle or often overlooked points. Format the output as an HTML unordered list (<ul><li>...</li></ul>) without any additional text or explanations."
# - Always be formatted as an HTML unordered list: <ul><li>...</li></ul>.
    
    
    
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": content}],
    }
    response_json = requests.post(url, headers=headers, json=data).json()
    answer_content = response_json["choices"][0]["message"]["content"]
    answer = answer_content.split('</think>\n')[1] if '</think>\n' in answer_content else answer_content
    return answer

async def deepSeek(input, course, course_id, topic_name, topic_description, internet_toggle, fileText):
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
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
    if fileText:
        content = f"When generating the answer, you must consider this file content as part of the topic context: {fileText}\n\n{content}"
    try:
        history = await CourseChatHistory.objects.aget(course_id=course_id)
    except:
        history = await CourseChatHistory.objects.acreate(course_id=course_id, history=[])
    history.history.append({"role": "user", 'message': input, "content": content})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": history.history,
        "web_search": internet_toggle,
    }
    response_json = requests.post(url, headers=headers, json=data).json()
    answer_content = response_json["choices"][0]["message"]["content"]
    answer = answer_content.split('</think>\n')[1] if '</think>\n' in answer_content else answer_content
    return answer

async def sendMessage(request):
    if request.method == 'POST':
        form = AIForm(request.POST, request.FILES)
        if form.is_valid():
            input = form.cleaned_data['prompt']
            course = form.cleaned_data['course']
            course_id = form.cleaned_data['course_id']
            topic_name = form.cleaned_data['topic_name']
            topic_description = form.cleaned_data['topic_description']
            internet_toggle = form.cleaned_data['internet_toggle']
            if form.cleaned_data['file']:
                fileText = ''
                uploaded_file = form.cleaned_data['file']
                for chunk in uploaded_file.chunks():
                    fileText += chunk.decode('utf-8')
            else:
                fileText = ''
            answer = await deepSeek(input, course, course_id, topic_name, topic_description, internet_toggle, fileText)
            return JsonResponse({'message': answer})
        else:
            return JsonResponse({'message': form.errors})
    return JsonResponse({'message': 'Invalid request'})


api_key = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjliMTVlODBmLWY3ODUtNDEzYy1hZjhiLTE5NDU4ODI5MTY4NSIsImV4cCI6NDkwNDUzOTE2N30.Xo4MbPTYxcjEq1TMwNQ_YTrGalMEn7U4oDOiadVsSnJbZiK_pRvh4pBU6UH8qr9uaVOKc1ryW6Yc--7ih0Ec6Q'

# Градиент — это вектор, указывающий направление наибольшего возрастания функции. Для функции нескольких переменных f(x, y, z...) градиент ∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z, ...) состоит из её частных производных. Он показывает, как и куда функция возрастает быстрее всего. Если градиент равен нулю, это может быть точка экстремума.