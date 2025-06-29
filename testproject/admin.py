from django.contrib import admin  
from .models import User, Courses, CourseChatHistory, Topic, Test
admin.site.register(User)
admin.site.register(Courses)
admin.site.register(CourseChatHistory)
admin.site.register(Topic)
admin.site.register(Test)