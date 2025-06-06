from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30)
    # password = models.CharField()
    # bio = models.TextField()
    intField = models.IntegerField(default=0)