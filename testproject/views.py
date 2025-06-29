from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from openai import OpenAI
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm, LoginForm, AddCourseForm, AIForm, AddTestForm, AddTopicForm
from .models import User, Courses, CourseChatHistory, Topic
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
        return render(request, 'signup.html', {'signup_form' : SignUpForm})


def login(request):
    # getting data from login_form
    login_form = LoginForm(data = request.POST)

    # trying to authenticate
    if login_form.is_valid():
        username = login_form.cleaned_data['username']
        password = login_form.cleaned_data['password']

        user = auth.authenticate(username=username, password=password)

        # if such user exists than authenticate
        if user:
            auth.login(request, user)
            return redirect(reverse('home'))
    
    # if authentication failed than hust return main page
    return render(request, 'login.html', {'login_form': LoginForm})

def logout(request):
    auth.logout(request)
    return redirect(reverse('index'))


# Вот кому-то делать нехуй

def printAllUsers():
    for el in User.objects.all():
        print(el.username)

def testUser():
    testUser = User.objects.get(username='test')
    if testUser:
        print('User \'test\' exists')
    else: print('nah')

def superUsers():
    su = User.objects.filter(is_superuser=True)
    for el in su:
        print(el.username)
    else:
        print('No super users')

def courses (request):
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
            print(new_name, new_desc)
            courses = Courses.objects.filter(id=course_id)
            if courses:
                courses[0].name = new_name
                courses[0].description = new_desc
                courses[0].save()
        elif 'delete_course' in request.POST:
            course_id = request.POST['delete_course']
            courses = Courses.objects.filter(id=course_id)
            if courses:
                courses[0].delete()
    return render (request, "courses.html", { "courses": Courses.objects.filter(user_id=auth.get_user(request).user_id), "form": AddCourseForm})

def donat(request):
    return render(request, 'donat.html')
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
                # print(name, description, topic_id)
                Topic.objects.create(topic_id=topic_id, course_id=course_id, user_id=auth.get_user(request).user_id, name=name, description=description)
                return redirect(reverse('course', args=(course_id,)))
            else:
                print(form.errors)
    if Courses.objects.filter(course_id=course_id).exists():
        course = Courses.objects.get(course_id=course_id)
    else:
        return redirect(reverse('courses'))
    topics = Topic.objects.filter(course_id=course_id)
    return render(request, 'course.html', {'form': AIForm, 'addTopicForm': AddTopicForm, 'addTestForm': AddTestForm, 'course': course, 'topics': topics})


def topic(request, course_id, topic_id):
    if Courses.objects.filter(course_id=course_id).exists() and Topic.objects.filter(topic_id=topic_id):
        course = Courses.objects.get(course_id=course_id)
        topic = Topic.objects.get(topic_id=topic_id)
    else:
        return redirect(reverse('courses'))
    topics = Topic.objects.filter(course_id=course_id)
    return render(request, 'course.html', {'form': AIForm, 'addTopicForm': AddTopicForm, 'addTestForm': AddTestForm, 'course': course, 'topics': topics, 'topic': topic})
    
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

async def chatGPT(input, course, course_id, topic_name, topic_description, internet_toggle, fileText):
    client = Client()
    content = f'Отправь ответ пользователю, по теме "{topic_name}" из курса "{course}", конспект которой:\n {topic_description}\n\nЕсли вопрос не по теме, напиши, что он не по теме. Напиши только ответ на вопрос, начиная с "Ответ: "!!!. Вот вопрос: {input}'
    if fileText:
        content = 'Вместе с данными из файла, ' + fileText + ',' + content
    try:
        history = await CourseChatHistory.objects.aget(course_id=course_id)
    except:
        history = await CourseChatHistory.objects.acreate(course_id=course_id, history=[])
    if not internet_toggle:
        history.history.append({"role": "user", 'message': input, "content": content})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            web_search = False
        )
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            content = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: (get_search_message(content))
        )
        history.history.append({"role": "user", 'message':input, "content": content + "Ни в коем случае не забудь вывести источники!!"})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history,
            web_search = True
        )
    history.history.append({'role': 'assistant', 'message': response.choices[0].message.content, 'content': response.choices[0].message.content})
    await history.asave()
    return response
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
            response = await chatGPT(input, course, course_id, topic_name, topic_description, internet_toggle, fileText)
            return JsonResponse({'message': response.choices[0].message.content})
        else:
            return JsonResponse({'message': form.errors})
    return JsonResponse({'message': 'Invalid request'})


api_key = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjliMTVlODBmLWY3ODUtNDEzYy1hZjhiLTE5NDU4ODI5MTY4NSIsImV4cCI6NDkwNDUzOTE2N30.Xo4MbPTYxcjEq1TMwNQ_YTrGalMEn7U4oDOiadVsSnJbZiK_pRvh4pBU6UH8qr9uaVOKc1ryW6Yc--7ih0Ec6Q'
def req():
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": "can you please provide for me html code with conspect about limits?"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    return response.json()
