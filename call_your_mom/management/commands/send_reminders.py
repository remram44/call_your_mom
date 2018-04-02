import datetime
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

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
                    subject="Reminder - {0}".format(task.name),
                    message="You asked to be reminded of this task by Call "
                            "Your Mom.\n\n"
                            "{0}\n\n"
                            "Follow this link to mark this as done and prime "
                            "the next reminder:\n    {1}\n".format(
                        task.description,
                        link,
                    ),
                    from_email=settings.EMAIL_FROM,
                    recipient_list=[task.user.email],
                )
                task.reminded = now
                task.save()
