from django.contrib import admin

from .models import CYMUser, Task, TaskDone


admin.site.register(CYMUser)
admin.site.register(Task)
admin.site.register(TaskDone)
