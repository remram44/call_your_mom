import datetime
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseNotFound
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import translation
from django.utils.translation import gettext as _

from .auth import needs_login, send_login_email, send_register_email, \
    clear_login
from .models import CYMUser, Task


def index(request):
    """Website index, redirects either to landing page or profile.
    """
    if request.cym_user is not None:
        return redirect('profile', permanent=False)
    else:
        return redirect('landing', permanent=False)


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
        else:
            # If the user never logged in, delete it
            if user.last_login is None:
                user.delete()
                user = None

        if user is not None:
            send_login_email(user)
        else:
            user = CYMUser(
                email=email,
                created=datetime.datetime.now(),
                last_login_email=datetime.datetime.now(),
            )
            user.save()
            send_register_email(user)

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
            send_login_email(user, path)

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


@needs_login
def profile(request):
    """A user's profile, listing all his tasks.
    """
    return render(request, 'call_your_mom/profile.html',
                  {'cym_user': request.cym_user,
                   'tasks': request.cym_user.task_set.all()})


@needs_login
def change_task(request, task_id):
    """Creation or modification of a task.

    Note that this is different from acknowledgement page, linked from reminder
    emails.
    """
    if task_id == 'new':
        task = None
    else:
        try:
            task = Task.objects.get(id=int(task_id))
        except (ObjectDoesNotExist, ValueError):
            task = None
        if not task or task.user.id != request.cym_user.id:
            return HttpResponseNotFound(_("Couldn't find this task!"))

    # TODO: Create or edit task

    return render(request, 'call_your_mom/change_task.html',
                  {'task': task})


@needs_login
def delete_task(request, task_id):
    """Delete a task.
    """
    # TODO: Delete task if user's
    return redirect('index', permanent=False)


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

    # TODO: Ack task form if user's

    return render(request, 'call_your_mom/acknowledge_task.html',
                  {'task': task,
                   'today': datetime.date.today()})


def set_lang(request, lang):
    """Change the language.
    """
    translation.activate(lang)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect('index', permanent=False)
