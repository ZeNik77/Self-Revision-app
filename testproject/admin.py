from django.contrib import admin  
from .models import User, Courses, CourseChatHistory, Topic
admin.site.register(User)
admin.site.register(Courses)
admin.site.register(CourseChatHistory)
admin.site.register(Topic)