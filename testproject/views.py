from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm, LoginForm, AddCourseForm, AIForm
from .models import User, Courses
from g4f.client import Client
from g4f.gui.server.internet import get_search_message
import random
import asyncio

def index(request):
    # processing POST request
    if request.method == 'POST':
        if 'login' in request.POST:
            login(request)
        elif 'register' in request.POST:
            signup(request)

    # redirecting to login page
    return redirect(reverse(login))

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
                course_id = random.randint(2, 10000000000)
                while Courses.objects.filter(course_id=course_id).exists():
                    course_id = random.randint(2, 10000000000)
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
    return render (request, "courses.html", { "courses": Courses.objects.filter(user_id=auth.get_user(request).user_id), "form": AddCourseForm })

def donat(request):
    return render(request, 'donat.html')
def course(request, course_id):
    if Courses.objects.filter(course_id=course_id).exists():
        course = Courses.objects.get(course_id=course_id)
    else:
        return redirect(reverse('courses'))
    gradient_summary = "Градиент — это вектор, указывающий направление наибольшего возрастания функции. Для функции нескольких переменных f(x, y, z...) градиент ∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z, ...) состоит из её частных производных. Он показывает, как и куда функция возрастает быстрее всего. Если градиент равен нулю, это может быть точка экстремума."
    return render(request, 'course.html', {'form': AIForm, 'course': course.name, 'topic_name': 'Градиент', 'topic_description': gradient_summary})

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

async def chatGPT(input, course, topic_name, topic_description, internet_toggle, fileText):
    client = Client()
    content = f'Отправь ответ пользователю, по теме "{topic_name}" из курса "{course}", конспект которой:\n {topic_description}\n\nЕсли вопрос не по теме, напиши, что он не по теме. Напиши только ответ на вопрос, начиная с "Ответ: "!!!. Вот вопрос: {input}'
    # content = input
    if fileText:
        content = 'Вместе с данными из файла, ' + fileText + ',' + content
    if not internet_toggle:
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": content + "Ни в коем случае не забудь вывести источники!!"
                }
            ],
            web_search = True
        )
    return response
async def sendMessage(request):
    if request.method == 'POST':
        form = AIForm(request.POST, request.FILES)
        if form.is_valid():
            input = form.cleaned_data['prompt']
            course = form.cleaned_data['course']
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
            response = await chatGPT(input, course, topic_name, topic_description, internet_toggle, fileText)
            return JsonResponse({'message': response.choices[0].message.content})
        else:
            return JsonResponse({'message': form.errors})
    return JsonResponse({'message': 'Invalid request'})