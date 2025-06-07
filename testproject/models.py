from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # id = models.BigAutoField(primary_key=True)
    # password = models.CharField()
    # bio = models.TextField()
    intField = models.IntegerField(default=0)

class Courses(models.Model):
    name = models.CharField()
    description = models.TextField()