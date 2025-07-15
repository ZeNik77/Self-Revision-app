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
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'signup_username'
        })
    )

    # password form
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'signup_password1'
        })
    )

    # confirm_password form
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
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
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'login_username'
        })
    )

    # password form
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
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
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter course name'
        })
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block p-2.5 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Enter course description',
            'rows': 1
        })
    )

class AIForm(forms.Form):
    prompt = forms.CharField(
        label="Your Prompt",
        required=False,
        widget=forms.Textarea(
            attrs={
                "id": "aiInput",
                "class": "w-full p-2 border rounded-md focus:outline-none focus:ring focus:ring-indigo-200 text-sm resize-none",
                "rows": 3,
                "placeholder": "Ask your question..."
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
    course = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'courseText', 'class': 'hidden'}))
    course_id = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'id': 'course_idText', 'class': 'hidden'}))
    topic_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_nameText', 'class': 'hidden'}))
    topic_description = forms.CharField(required=False, widget=forms.TextInput(attrs={'id': 'topic_descriptionText', 'class': 'hidden'}))

class AddTopicForm(forms.Form):
    topic_name = forms.CharField(
        label="Topic Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full mb-4 px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:ring-indigo-200',
            'placeholder': 'Enter topic name',
            'id': 'topic_name'
        })
    )

class TestForm2(forms.Form):
  def __init__(self, *args, **kwargs):
    questions = kwargs.pop('questions')
    self.correct = kwargs.pop('correct')
    super(TestForm2, self).__init__(*args, **kwargs)
    for i, q in enumerate(questions, start=0):
        field_name = f"question_{i}"
        self.fields[field_name] = forms.ChoiceField(
            label=q["question"],
            choices=[(a, a) for a in q["answer"]],
            widget=forms.RadioSelect(attrs={"class": "mr-2", "id": field_name}),
            required=True
        )
class RAGForm(forms.Form):
    file = forms.FileField(
        label="Upload Course content",
        # max_size=5*1024*1024,
        # allowed_extensions=['pdf', 'docx', 'txt'],
        widget=forms.ClearableFileInput(
            attrs={
                "id": "fileInput",
                'type': 'file',
                # "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400",
            }
        )
    )