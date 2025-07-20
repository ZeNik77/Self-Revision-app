from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib import auth
from django.urls import reverse
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
from .forms import SignUpForm, LoginForm, AddCourseForm, AIForm, AddTopicForm, TestForm2, RAGForm, SaveTopicForm, SaveRevisionForm, UserPFPForm
from .models import User, Courses, CourseChatHistory, Topic, Test
from .generate import revise, deepSeek, generateTest, divideToSubtopics
import random
import os
import json

from django.middleware.csrf import CsrfViewMiddleware
def check_csrf(request):
    """Returns True if CSRF check passes, False otherwise."""
    # Provide a dummy get_response callable
    middleware = CsrfViewMiddleware(get_response=lambda req: None)
    dummy_view = lambda req: None
    # Run CSRF check
    response = middleware.process_view(request, dummy_view, (), {})
    return response is None
def profile(request):
    user = auth.get_user(request)
    results = []

    if request.method == "POST":
        # Загрузка аватарки
        if 'avatar' in request.POST:
            form = UserPFPForm(request.POST, request.FILES)
            if form.is_valid():
                request.user.avatar = form.cleaned_data['file']
                request.user.save()
            else:
                print(form.errors)
        if 'submit_seeResults' in request.POST:
            subtopic_id = request.POST.get("subtopic")
            try:
                results = Test.objects.filter(topic_id=subtopic_id, passed=True)
                for test in results:
                    qlist = []
                    correct_map = {q["question"]: q["answer"] for q in test.correctQuestions or []}
                    incorrect_map = {q["question"]: (q["answer"], q["correct"]) for q in test.incorrectQuestions or []}
                    for q in test.questions:
                        opts = q.get("answer", [])
                        text = q.get("question", "")
                        if text in correct_map:
                            user_ans = correct_map[text]
                            qlist.append({"question": text, "options": opts, "user_answer": user_ans, "correct": user_ans})
                        elif text in incorrect_map:
                            user_ans, correct_ans = incorrect_map[text]
                            qlist.append({"question": text, "options": opts, "user_answer": user_ans, "correct": correct_ans})
                        else:
                            qlist.append({"question": text, "options": opts, "user_answer": None, "correct": None})
                    test.questions = qlist
            except:
                return JsonResponse(data={'error': 'UNKNOWN ERROR'}, status=500)

    courses = Courses.objects.all()
    return render(request, "profile.html", {
        "user": user,
        "courses": courses,
        "results": results,
        'pfpForm': UserPFPForm
    })
# понятия не имею правильно ли я подключила, но работает криво? можно убрать и оставить дефолтную аватарку

def index(request):
    # processing POST request
    if request.method == 'POST':
        if 'login' in request.POST:
            login(request)
        elif 'register' in request.POST:
            signup(request)

    # redirecting to login page
    return redirect(reverse('home'))
    # return redirect(reverse('login'))

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

def terms(request):
    return render(request, 'terms_conditions.html')

def privacy(request):
    return render(request, 'privacy.html')

# Вот кому-то делать нехуй
# наверное )

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
            topics = Topic.objects.filter(course_id=course_id).order_by('topic_id')
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

def add_topic(request, course_id, topic_id=-1):
    form = AddTopicForm(data=request.POST)
    if form.is_valid():
        name = form.cleaned_data['topic_name']
        topic_id = random.randint(2, 2147483646)
        while Topic.objects.filter(topic_id=topic_id).exists():
            topic_id = random.randint(2, 2147483646)
        Topic.objects.create(topic_id=topic_id, course_id=course_id, user_id=auth.get_user(request).user_id, name=name, description='')
        if topic_id == -1:
            return redirect(reverse('course', args=[course_id]))
        else:
            return redirect(reverse('topic', args=[course_id, topic_id]))
    else:
        print(form.errors)
def delete_topic(request, course_id, topicId=-1):
    topic_id = request.POST['delete_topic']
    topic = Topic.objects.filter(topic_id=topic_id)
    tests = Test.objects.filter(topic_id=topic_id)
    for el in tests:
        el.delete()
    if topic:
        topic[0].delete()
    if topicId == -1:
        return redirect(reverse('course', args=[course_id]))
    else:
        return redirect(reverse('topic', args=[course_id, topicId]))
def course(request, course_id):
    notification = ''
    if request.method == 'POST':
        if 'add_topic' in request.POST:
            x = add_topic(request, course_id)
            if x:
                return x
        if 'delete_topic' in request.POST:
            return delete_topic(request, course_id)
        if 'add_topics_file' in request.POST:
            result = add_outline(request, course_id)
            if result == False:
                notification = 'No topics found.'
            elif result:
                return result
    if Courses.objects.filter(course_id=course_id).exists():
        course = Courses.objects.get(course_id=course_id)
    else:
        return redirect(reverse('courses'))
    topics = Topic.objects.filter(course_id=course_id).order_by('topic_id')
    return render(request, 'course.html', {
        'form': AIForm,
        'addTopicForm': AddTopicForm,
        'rag_form': RAGForm,
        'course': course,
        'topics': topics,
        'notification': notification
    })

def save_file(uploaded_file):
    fs = FileSystemStorage()
    # Сохраняем
    return fs.save(uploaded_file.name, uploaded_file)

def add_outline(request, course_id, topic_id=-1):
    if check_csrf(request):
        ln = len(Topic.objects.filter(course_id=course_id).all())
        form = RAGForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            file_path = save_file(uploaded_file)
            divideToSubtopics(file_path, course_id, auth.get_user(request).user_id)
        else:
            print(form.errors)
        ln2 = len(Topic.objects.filter(course_id=course_id).all())
        if ln == ln2:
            print('none was generated, returned False')
            return False
        print('generated fine')
    else:
        if topic_id != -1:
            print('redirected to topic')
            return redirect(reverse('topic', args=[course_id, topic_id]))
        else:
            print('redirected to course')
            return redirect(reverse('course', args=[course_id]))

def topic(request, course_id, topic_id):
    notification = ''
    testError = ''
    if not auth.get_user(request).is_active or not Courses.objects.filter(user_id=auth.get_user(request).user_id, course_id=course_id).exists():
        return redirect(reverse('courses'))
    elif not Topic.objects.filter(user_id=auth.get_user(request).user_id, topic_id=topic_id).exists():
        return redirect(reverse('course', args=[course_id]))
    else:
        course = Courses.objects.get(course_id=course_id)
        topic = Topic.objects.get(topic_id=topic_id)
    
    if request.method == 'POST':
        # TODO: restrict repeated form submission
        if 'add_topic' in request.POST:
            x = add_topic(request, course_id, topic_id)
            if x:
                return x
        if 'delete_topic' in request.POST:
            return delete_topic(request, course_id, topic_id)
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
                notification = 'Created a test. Click "Test" button again.'
            except:
                notification = 'Failed to create a test'
        if 'submit_revision' in request.POST:
            course = Courses.objects.get(course_id=course_id)
            topic = Topic.objects.get(topic_id=topic_id)
            topic.revision = revise(course.name, topic.name, topic.description)
            topic.save()
            notification = 'Created a revision. Click "Revise" button again'
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
                notification = 'Test result is saved. See it in your profile, via this subtopic.'
            else:
                print(form.errors)

        if 'delete_topic' in request.POST:
            t_id = request.POST['delete_topic']
            delete_topic(t_id)
            return redirect(reverse('topic', args=(course_id, topic_id)))
        if 'delete_test' in request.POST:
            test_id = request.POST['delete_test']
            if (test := Test.objects.filter(test_id=test_id)).exists():
                test.delete()
        if 'add_topics_file' in request.POST:
            result = add_outline(request, course_id, topic_id)
            if result == False:
                notification = 'No topics found.'
            elif result:
                return result
        if 'save_topic' in request.POST:
            form = SaveTopicForm(request.POST)
            if form.is_valid():
                description = form.cleaned_data['description']
                topic.description = description
                topic.save()
            else:
                print(form.errors)
        if 'save_revision' in request.POST:
            form = SaveRevisionForm(request.POST)
            if form.is_valid():
                revision = form.cleaned_data['revision']
                topic.revision = revision
                topic.save()
            else:
                print(form.errors)
    topics = Topic.objects.filter(course_id=course_id).order_by('topic_id')
    test = Test.objects.filter(topic_id=topic_id, passed=False)
    passed_tests = Test.objects.filter(topic_id=topic_id, passed=True)
    if not test.exists():
        test = None
        testForm = None
        correct = None
        questions = None
    else:
        test = test.last()
        testForm = TestForm2(questions=test.questions, correct=test.correct)
        correct = test.correct
        questions = test.questions
    revision = topic.revision
    print(revision, '\n', f'"{revision.strip()}"')
    if revision.replace('<br>', '').strip() == '':
        revision = ''
        topic.revision = ''
        topic.save()
    return render(request, 'course.html', {
        'form': AIForm, 
        'addTopicForm': AddTopicForm, 
        'rag_form': RAGForm, 
        'saveTopicForm': SaveTopicForm,
        'saveRevisionForm': SaveRevisionForm,
        'course': course, 
        'topics': topics, 
        'topic': topic, 
        'test': test, 
        'test_form': testForm, 
        'correct': json.dumps(correct), 
        'questions': json.dumps(questions), 
        'revision': revision, 
        'passed_tests': passed_tests, 
        'test_error': testError,
        'notification': notification
    })
    
def home(request):
    if auth.get_user(request).is_active:
        return render(request, 'landing.html')
    else:
        return redirect(reverse('login'))

def about(request):
    return render(request, 'about.html')


def sendMessage(request):
    if request.method == 'POST':
        form = AIForm(request.POST, request.FILES)
        if form.is_valid():
            input = form.cleaned_data['prompt']
            course = form.cleaned_data['course']
            course_id = form.cleaned_data['course_id']
            topic_name = form.cleaned_data['topic_name']
            topic_description = form.cleaned_data['topic_description']
            internet_toggle = form.cleaned_data['internet_toggle']
            file_path = ''
            if form.cleaned_data['file']:
                uploaded_file = form.cleaned_data['file']
                file_path = save_file(uploaded_file)
            answer = deepSeek(input, course, course_id, topic_name, topic_description, internet_toggle, file_path)
            return JsonResponse({'message': answer}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def seeTopics(request):
    if request.method == 'POST':
        if 'id' in request.POST:
            courseId = int(request.POST['id'])
            try:
                topics = Topic.objects.filter(course_id=courseId).order_by('topic_id').all()
                topics = [{'name': el.name, 'topic_id': el.topic_id} for el in topics]
                return JsonResponse({'topics': topics}, status=200)
            except:
                return JsonResponse({'error': 'Unknown error'}, status=500)
        else:
            return JsonResponse({'error': 'No ID in the request'}, status=400)

# Градиент — это вектор, указывающий направление наибольшего возрастания функции. Для функции нескольких переменных f(x, y, z...) градиент ∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z, ...) состоит из её частных производных. Он показывает, как и куда функция возрастает быстрее всего. Если градиент равен нулю, это может быть точка экстремума.

def seeStatus(request):
    oldStatus = cache.get('divideIntoSubtopicsStatusOld')
    status = cache.get('divideIntoSubtopicsStatus')
    if status == oldStatus:
        return JsonResponse({}, status=200)
    cache.set('divideIntoSubtopicsStatusOld', status)
    return JsonResponse({'status': status}, status=200)