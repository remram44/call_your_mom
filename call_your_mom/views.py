import datetime
import dateutil.parser
import pytz
import pytz.exceptions
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from .auth import needs_login, send_login_email, send_register_email, \
    clear_login, EmailRateLimit
from .models import CYMUser, Task, TaskDone


def index(request):
    """Website index, redirects either to landing page or profile.
    """
    if request.cym_user is not None:
        return redirect('profile')
    else:
        return redirect('landing')


def landing(request):
    """The landing page, giving a description of what this is.
    """
    return render(request, 'call_your_mom/landing.html')


def register(request):
    """Registration-or-login page, via which users sign up for the website.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email or len(email) < 3:
            messages.add_message(request, messages.ERROR,
                                 _("Please provide an email address"))
            return redirect('register')

        # Find out if an account exists for the email
        try:
            user = CYMUser.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None

        try:
            if user is not None:
                send_login_email(user)
                user.last_login_email = timezone.now()
                user.save()
            else:
                user = CYMUser(
                    email=email,
                    created=timezone.now(),
                    last_login_email=timezone.now(),
                )
                send_register_email(user)
                user.save()
        except EmailRateLimit:
            messages.add_message(
                request, messages.ERROR,
                _("Rate-limiting is active. Not sending another email to "
                  "{0}.").format(user.email))
            return redirect('confirm')

        messages.add_message(
            request, messages.INFO,
            _("We have sent an email to {0}. Please follow the link inside to "
              "start creating tasks.").format(email))
        return redirect('confirm')
    else:
        return render(request, 'call_your_mom/register.html')


def login(request):
    """Login page.

    Prompt the user for an email address, to which a log-in link will be sent.
    """
    path = request.GET.get('path', '')

    if request.method == 'POST':
        email = request.POST.get('email')
        if not email or len(email) < 3:
            messages.add_message(request, messages.ERROR,
                                 _("Please provide an email address"))
            return redirect('login', path=path)

        # Find out if an account exists for the email
        try:
            user = CYMUser.objects.get(email=email)
        except ObjectDoesNotExist:
            pass
        else:
            try:
                send_login_email(user, path)
                user.last_login_email = timezone.now()
                user.save()
            except EmailRateLimit:
                messages.add_message(
                    request, messages.ERROR,
                    _("Rate-limiting is active. Not sending another email to "
                      "{0}.").format(user.email))
                return redirect('confirm')

        messages.add_message(
            request, messages.INFO,
            _("We have sent an email to {0}, if such an account exist. Please "
              "follow the link inside to log in.").format(email))
        return redirect('confirm')
    else:
        return render(request, 'call_your_mom/login.html')


def logout(request):
    """Log out the current user.
    """
    clear_login(request)
    messages.add_message(request, messages.INFO,
                         _("You have been logged out."))
    return redirect('confirm')


def confirm(request):
    """Confirmation page, no userful content but displays messages.
    """
    return render(request, 'call_your_mom/confirm.html')


_somedate = datetime.datetime(2018, 1, 2, 13, 0)
_timezones = []
for name in pytz.common_timezones:
    tz = pytz.timezone(name)
    offset = tz.utcoffset(_somedate) - tz.dst(_somedate)
    offset = orig = int(offset.total_seconds())

    offset_str = '+'
    if offset < 0:
        offset = -offset
        offset_str = '-'
    offset_str = '{}{:02}:{:02}'.format(offset_str,
                                        offset // 3600,
                                        (offset // 60) % 60)

    _timezones.append((orig, offset_str, name))
_timezones = [(n, s) for (o, s, n) in sorted(_timezones)]


@needs_login
def profile(request):
    """A user's profile, listing all his tasks.
    """
    if request.method == 'POST':
        if 'timezone' in request.POST:
            try:
                tz = pytz.timezone(request.POST['timezone'])
            except pytz.exceptions.UnknownTimeZoneError:
                pass
            else:
                request.cym_user.timezone = tz
                request.cym_user.save()
                messages.add_message(
                    request, messages.INFO,
                    _("Timezone updated"))
        redirect('profile')

    return render(request, 'call_your_mom/profile.html',
                  {'cym_user': request.cym_user,
                   'tasks': request.cym_user.task_set.all(),
                   'timezones': _timezones})


@needs_login
def change_task(request, task_id):
    """Creation or modification of a task.

    Note that this is different from acknowledgement page, linked from reminder
    emails.
    """
    if task_id == 'new':
        task = None
        task_done_previously = []
    else:
        try:
            task_id = int(task_id)
            task = Task.objects.get(id=task_id)
        except (ObjectDoesNotExist, ValueError):
            task = None
        if not task or task.user.id != request.cym_user.id:
            return HttpResponseNotFound(_("Couldn't find this task!"))

        task_done_previously = (
            TaskDone.objects.filter(task=task)
            .order_by('-done')
            .all()[:30]
        )

    if request.method == 'POST':
        task_name = request.POST.get('name', '')
        task_description = request.POST.get('description', '')
        task_due = request.POST.get('due', '')
        task_interval_days = request.POST.get('interval_days', '')

        valid = True

        if not task_name:
            messages.add_message(request, messages.ERROR,
                                 _("Please give your task a name"))
            valid = False

        if task_due:
            try:
                task_due = dateutil.parser.parse(task_due).date()
            except ValueError:
                task_due = None
        if not task_due:
            messages.add_message(request, messages.ERROR,
                                 _("Please give your task a due date"))
            if task:
                task_due = task.due
            else:
                task_due = (timezone.now() +
                            datetime.timedelta(days=task_interval_days))
                task_due = timezone.make_naive(task_due)
            valid = False

        if task_interval_days:
            try:
                task_interval_days = int(task_interval_days)
            except ValueError:
                task_interval_days = None
            if task_interval_days < 1:
                task_interval_days = None
        if not task_interval_days:
            messages.add_message(request, messages.ERROR,
                                 _("Please give your task an interval in days "
                                   "between occurrences"))
            task_interval_days = 7
            valid = False

        if valid:
            if task:
                task.name = task_name
                task.description = task_description
                task.interval_days = task_interval_days
                task.due = task_due
                task.save()
                messages.add_message(request, messages.INFO,
                                     _("Task updated"))
            else:
                task = Task(user_id=request.cym_user.id,
                            name=task_name,
                            description=task_description,
                            interval_days=task_interval_days,
                            due=task_due)
                task.save()
                messages.add_message(request, messages.INFO,
                                     _("Task created"))
            return redirect('profile')
    elif task:
        task_name = task.name
        task_description = task.description
        task_interval_days = task.interval_days
        task_due = task.due
    else:
        task_name = ''
        task_description = ''
        task_interval_days = 7
        task_due = (timezone.now() +
                    datetime.timedelta(days=task_interval_days))
        task_due = timezone.make_naive(task_due).date()

    return render(request, 'call_your_mom/change_task.html',
                  {'task_id': task_id,
                   'task_name': task_name,
                   'task_description': task_description,
                   'task_interval_days': task_interval_days,
                   'task_due': task_due,
                   'task_is_due': task.is_due(request.cym_user.timezone),
                   'task_done_previously': task_done_previously,
                   'new': task is None})


@needs_login
def delete_task(request, task_id):
    """Delete a task.
    """
    try:
        task_id = int(task_id)
        task = Task.objects.get(id=task_id)
    except (ObjectDoesNotExist, ValueError):
        task = None
    if not task or task.user.id != request.cym_user.id:
        return HttpResponseNotFound(_("Couldn't find this task!"))

    task.delete()
    messages.add_message(request, messages.INFO,
                         _("Task deleted"))

    return redirect('profile')


@needs_login
def ack_task(request, task_id):
    """Acknowledge a task, from a reminder.

    This is the page that reminder emails link to. It allows the user to set
    when the task was done, and when it is due next.
    """
    try:
        task = Task.objects.get(id=task_id)
    except ObjectDoesNotExist:
        task = None
    if not task or task.user.id != request.cym_user.id:
        return HttpResponseNotFound(_("Couldn't find this task!"))

    if task and request.method == 'POST':
        task_done = request.POST.get('done', '')
        task_due = request.POST.get('due', '')

        valid = True

        if task_done:
            try:
                task_done = dateutil.parser.parse(task_done).date()
            except ValueError:
                task_done = None
        if not task_done:
            messages.add_message(request, messages.ERROR,
                                 _("Please enter the date you performed the "
                                   "task"))
            task_done = timezone.make_naive(timezone.now()).date()
            valid = False

        if task_due:
            try:
                task_due = dateutil.parser.parse(task_due).date()
            except ValueError:
                task_due = None
        if not task_due:
            messages.add_message(request, messages.ERROR,
                                 _("Please enter the date this task is due "
                                   "next"))
            task_due = task_done + datetime.timedelta(days=task.interval_days)
            valid = False

        if valid:
            done = TaskDone(task=task, done=task_done)
            done.save()

            task.due = task_due
            task.save()

            return redirect('profile')
    else:
        task_done = timezone.make_naive(timezone.now()).date()
        task_due = task_done + datetime.timedelta(days=task.interval_days)

    return render(request, 'call_your_mom/ack_task.html',
                  {'task': task,
                   'task_done': task_done,
                   'task_due': task_due,
                   'task_is_due': task.is_due(request.cym_user.timezone)})


def set_lang(request, lang):
    """Change the language.
    """
    translation.activate(lang)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang
    if request.cym_user:
        request.cym_user.language = lang
        request.cym_user.save()
    return redirect('index')
