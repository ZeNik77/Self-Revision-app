from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm, LoginForm, AddCourseForm
from .models import User, Courses

def index(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(data=request.POST)
        if form.is_valid():
            # На будущее - если захотим мб больше полей менять
            # user = form.save()
            # user.set_password(form.cleaned_data['field228'])
            # user.save()
            form.save()
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
        form = AddCourseForm(data=request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            desc = form.cleaned_data['description']
            Courses.objects.create(name=name, description=desc)
        else:
            print(form.errors)
    return render (request, "courses.html", { "courses": Courses.objects.all(), "form": AddCourseForm })
def donat(request):
    return render(request, 'donat.html')