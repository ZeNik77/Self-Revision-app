from django.http import HttpResponse
from django.shortcuts import render
from .forms import SignUpForm

def index(request):
    return render(request, 'index.html')

def signup(request):
    return render(request, 'signup.html', {'form': SignUpForm})