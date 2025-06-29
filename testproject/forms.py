from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.postgres.forms import SimpleArrayField
from .models import User

class SignUpForm(UserCreationForm):
    # username form
    username = forms.CharField(
        label='Username',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'id': 'signup_username'
        })
    )

    # password form
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'id': 'signup_password1'
        })
    )

    # confirm_password form
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'id': 'signup_password2'
        })
    )

    class Meta:
        model = User
        fields = ('username',)

class LoginForm(AuthenticationForm):
    # username form
    username = forms.CharField(
        label='Username',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'id': 'login_username'
        })
    )

    # password form
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'id': 'login_password1'
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
    course_id = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'id': 'course_idText', 'class': 'd-none'}))
    topic_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_nameText', 'class': 'd-none'}))
    topic_description = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_descriptionText', 'class': 'd-none'}))

class AddTestForm(forms.Form):
    course_id = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'id': 'course_idAddTest', 'class': 'd-none'}))
    topic_id = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'id': 'topic_idAddTest', 'class': 'd-none'}))
class TestForm(forms.Form):
    questions = forms.JSONField()

class AddTopicForm(forms.Form):
    topic_name = forms.CharField(
        label="Topic Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter topic name'
        })
    )

    topic_description = forms.CharField(
        label="Topic content",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter topic content',
            'rows': 1
        })
    )