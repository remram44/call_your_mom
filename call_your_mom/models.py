from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import Choices


class CYMUser(models.Model):
    email = models.CharField(max_length=200, primary_key=True)
    last_login = models.DateTimeField()
    last_email = models.DateTimeField()


class Task(models.Model):
    Type = Choices(('normal', _('normal')), ('exact', _('exact')))
    type = models.CharField(max_length=8, choices=Type)
    user = models.ForeignKey(CYMUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=280)
    created = models.DateTimeField()
    due = models.DateTimeField()


class TaskDone(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    done = models.DateTimeField()
    recorded = models.DateTimeField()
