import datetime
from django.shortcuts import redirect, render
from django.utils import translation

from .auth import needs_login


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
    """Registration page, via which users sign up for the website.
    """
    # TODO: Register, send email, log user in
    return render(request, 'call_your_mom/register.html')


@needs_login
def profile(request):
    """A user's profile, listing all his tasks.
    """
    # TODO: Get user's tasks
    return render(request, 'call_your_mom/profile.html')


@needs_login
def change_task(request, task_id):
    """Creation or modification of a task.

    Note that this is different from acknowledgement page, linked from reminder
    emails.
    """
    # TODO: Task edit form if user's
    return render(request, 'call_your_mom/change_task.html')


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
    # TODO: Ack task form if user's
    return render(request, 'call_your_mom/acknowledge_task.html')


def set_lang(request, lang):
    """Change the language.
    """
    translation.activate(lang)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return redirect('index', permanent=False)
