from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import User

class SignUpForm(forms.ModelForm):
    # username form
    username = forms.CharField(
        label='Username',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'username',
            'id': 'signup_username'
        })
    )

    # password form
    password1 = forms.CharField(
        label='Password',
        min_length=5,
        widget=forms.PasswordInput(attrs={
            'class': 'password',
            'id': 'signup_password1'
        })
    )

    # confirm_password form
    password2 = forms.CharField(
        label='Confirm Password',
        min_length=5,
        widget=forms.PasswordInput(attrs={
            'class': 'password',
            'id': 'signup_password2'
        })
    )

    class Meta:
        model = User
        fields = ('username',)

class LoginForm(AuthenticationForm):
    # username form
    username = forms.CharField(
        label='username',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'username',
            'id': 'login_username'
        })
    )

    # password form
    password = forms.CharField(
        label='password',
        min_length=5,
        widget=forms.PasswordInput(attrs={
            'class': 'password',
            'id': 'login_password'
        })
    )
    class Meta:
        model = User
        fields = ('username',)

class AddCourseForm(forms.Form):
    name = forms.CharField(
        label="Course Name",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter course name'
        })
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter course description',
            'rows': 1
        })
    )

class AIForm(forms.Form):
    prompt = forms.CharField(
        label="Your Prompt",
        widget=forms.Textarea(
            attrs={
                "id": "aiInput",
                "class": "form-control",
                "rows": 4,
                "placeholder": "Ask the AI anything..."
            }
        )
    )
    file = forms.FileField(
        label="Upload File",
        required=False,
        # max_size=5*1024*1024,
        # allowed_extensions=['pdf', 'docx', 'txt'],
        widget=forms.ClearableFileInput(
            attrs={
                "id": "fileInput",
                "class": "form-control",
            }
        )
    )
    internet_toggle = forms.BooleanField(
        label="Поиск 🔍",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch',
            'data-toggle': 'toggle',
            'id': 'internetToggle'
        })
    )
    course = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'courseText', 'class': 'd-none'}))
    topic_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_nameText', 'class': 'd-none'}))
    topic_description = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_descriptionText', 'class': 'd-none'}))
