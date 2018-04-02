import datetime
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils.translation import gettext as _

from website import settings
from ...auth import make_login_link
from ...models import Task


# FIXME: debug
def send_mail(**kwargs):
    print("WOULD SEND EMAIL")
    for k, v in kwargs.items():
        print("    {0}: {1}".format(k, v))


class Command(BaseCommand):
    help = "Cron command sending the reminder emails for tasks that are due"

    def handle(self, *args, **options):
        now = datetime.date.today()
        for task in Task.objects.all():
            self.stdout.write(self.style.NOTICE("Time now: {0}".format(now.isoformat())))
            self.stdout.write(self.style.NOTICE(
                "Task {0} due {1}. Is due: {2}, was reminded: {3}".format(
                    task.name, task.due.isoformat(),
                    "yes" if task.due <= now else "no",
                    "no" if (not task.reminded or task.reminded < task.due)
                    else "yes"
                )))
            if (task.due <= now and
                    (not task.reminded or task.reminded < task.due)):
                self.stdout.write(self.style.SUCCESS(
                    "Sending email to {0} for task {1}".format(
                        task.user.email,
                        task.name)))

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
                    from_email=settings.EMAIL_FROM,
                    recipient_list=[task.user.email],
                )
                task.reminded = now
                task.save()
