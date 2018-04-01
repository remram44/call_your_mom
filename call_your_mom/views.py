from django.shortcuts import redirect, render


def index(request):
    """Website index, redirects either to landing page or profile.
    """
    return redirect('landing', permanent=False)


def landing(request):
    """The landing page, giving a description of what this is.
    """
    return render(request, 'call_your_mom/landing.html')


def register(request):
    """Registration page, via which users sign up for the website.
    """
    return render(request, 'call_your_mom/register.html')


def profile(request):
    """A user's profile, listing all his tasks.
    """
    return render(request, 'call_your_mom/profile.html')


def change_task(request, task_id):
    """Creation or modification of a task.

    Note that this is different from acknowledgement page, linked from reminder
    emails.
    """
    return render(request, 'call_your_mom/change_task.html')


def ack_task(request, task_id):
    """Acknowledge a task, from a reminder.

    This is the page that reminder emails link to. It allows the user to set
    when the task was done, and when it is due next.
    """
    return render(request, 'call_your_mom/acknowledge_task.html')
