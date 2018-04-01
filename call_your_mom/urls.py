from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('landing', views.landing, name='landing'),
    path('register', views.register, name='register'),
    path('profile', views.profile, name='profile'),
    path('task/<int:task_id>', views.change_task, name='change_task'),
    path('ack/<int:task_id>', views.ack_task, name='ack_task'),
]
