from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.shortcuts import redirect
from .forms import SignUpForm
from .models import User

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
    return render(request, 'signup.html', {'form': SignUpForm})