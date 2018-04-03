import datetime
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from website import settings
from ...auth import make_login_link
from ...models import Task


class Command(BaseCommand):
    help = "Cron command sending the reminder emails for tasks that are due"

    def handle(self, *args, **options):
        now = datetime.date.today()
        for task in Task.objects.all():
            if (task.due <= now and
                    (not task.reminded or task.reminded < task.due)):
                self.stderr.write(self.style.SUCCESS(
                    "Sending email to {0} for task {1}".format(
                        task.user.email,
                        task.name)))

                translation.activate(task.user.language)
                link = reverse('ack_task', kwargs=dict(task_id=task.id))
                link = make_login_link(task.user.id, link)

                send_mail(
                    subject=_("Reminder - {0}").format(task.name),
                    message="{0}\n\n{1}\n\n{2}\n{3}".format(
                        _("You asked to be reminded of this task by Call "
                          "Your Mom."),
                        task.description,
                        _("Follow this link to mark this as done and prime "
                          "the next reminder:"),
                        link,
                    ),
                    html_message=render_to_string(
                        'call_your_mom/email_reminder.html',
                        {'name': task.name,
                         'description': task.description,
                         'link': link}),
                    from_email=settings.EMAIL_FROM,
                    recipient_list=[task.user.email],
                )
                task.reminded = now
                task.save()
