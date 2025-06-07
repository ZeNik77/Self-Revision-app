from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # id = models.BigAutoField(primary_key=True)
    # password = models.CharField()
    # bio = models.TextField()
    user_id = models.IntegerField(default=0)

class Courses(models.Model):
    course_id = models.IntegerField()
    name = models.CharField()
    description = models.TextField()
    user_id = models.IntegerField()
