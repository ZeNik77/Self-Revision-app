from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    # id = models.BigAutoField(primary_key=True)
    # password = models.CharField()
    # bio = models.TextField()
    user_id = models.IntegerField(default=0)

class Courses(models.Model):
    course_id = models.IntegerField()
    name = models.CharField(max_length=20)
    description = models.TextField()
    user_id = models.IntegerField()

class Topic(models.Model):
    topic_id = models.IntegerField()
    name = models.CharField(max_length=30)
    description = models.TextField()
    course_id = models.IntegerField()
    user_id = models.IntegerField()
class Test(models.Model):
    type = {'topic', 'course'}
    test_id = models.IntegerField()
    topic_id = models.IntegerField(default=-1)
    course_id = models.IntegerField(default=-1)
    user_id = models.IntegerField()
    name = models.CharField(max_length=30)
    questions = models.TextField()

class CourseChatHistory(models.Model):
    course_id = models.IntegerField()
    history = ArrayField(models.TextField())