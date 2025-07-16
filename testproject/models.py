from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    # id = models.BigAutoField(primary_key=True)
    # password = models.CharField()
    # bio = models.TextField()
    user_id = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

class Courses(models.Model):
    course_id = models.IntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField()
    user_id = models.IntegerField()

class Topic(models.Model):
    topic_id = models.IntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField()
    course_id = models.IntegerField()
    user_id = models.IntegerField()
    revisions = ArrayField(models.TextField(), default=list)

class CourseChatHistory(models.Model):
    course_id = models.IntegerField()
    history = ArrayField(models.JSONField())

class Test(models.Model):
    # type = {'topic', 'course'}
    test_id = models.IntegerField()
    topic_id = models.IntegerField()
    course_id = models.IntegerField()
    user_id = models.IntegerField()
    questions = models.JSONField()
    correct = ArrayField(models.TextField(), default=list)
    correctQuestions = models.JSONField(default=None)
    incorrectQuestions = models.JSONField(default=None)
    grade = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)