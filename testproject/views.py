from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm, LoginForm, AddCourseForm
from .models import User, Courses
import asyncio

def index(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(data=request.POST)
        if form.is_valid():
            if len(User.objects.all()) == 0:
                user_id = 1
            else:
                user_id = User.objects.all().last().user_id + 1
            user = form.save()
            user.user_id = user_id
            user.save()
            auth.login(request, user)
            return redirect(reverse('index'))
        
        else:
            return render(request, 'signup.html', {'form': form})
    return render(request, 'signup.html', {'form': SignUpForm})

def login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect(reverse('index'))
    return render(request, 'login.html', {'form': LoginForm})

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
                if len(Courses.objects.all()) == 0:
                    course_id = 0
                else:
                    course_id = Courses.objects.all().last().course_id + 1
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
def course(request):
    return render(request, 'course.html')
async def ajax_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        message = f'Welcome back, {name}!'
        print(message)
        await asyncio.sleep(3)
        return JsonResponse({'message': message})
    return JsonResponse({'message': 'Invalid request'})
