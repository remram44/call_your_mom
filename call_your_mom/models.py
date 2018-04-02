from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import Choices


class CYMUser(models.Model):
    class Meta:
        verbose_name = "User"

    USER_ID_KEY = 'cym_user_id'

    email = models.CharField(max_length=200, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True)
    last_login_email = models.DateTimeField()

    def __str__(self):
        return "<CYMUser id={0} email={1}>".format(self.id, self.email)


class Task(models.Model):
    Type = Choices(('normal', _('normal')), ('exact', _('exact')))
    type = models.CharField(max_length=8, choices=Type)
    user = models.ForeignKey(CYMUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=280)
    created = models.DateTimeField(auto_now_add=True)
    interval_days = models.IntegerField()
    due = models.DateField()
    reminded = models.DateField(null=True)


class TaskDone(models.Model):
    class Meta:
        verbose_name_plural = "Tasks done"

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    done = models.DateField()
    recorded = models.DateTimeField(auto_now_add=True)
