from base64 import b32encode, b32decode
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.signing import Signer
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import functools
import urllib.parse

from website import settings
from .models import CYMUser


class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Use a token to log in
        if 'token' in request.GET:
            token = request.GET['token']
            token = b32decode(token.upper().encode('ascii')).decode('ascii')
            user_id = Signer().unsign(token)
            request.cym_user = CYMUser.objects.get(id=user_id)
            request.cym_user.last_login = datetime.datetime.now()
            request.cym_user.save()
            request.session[CYMUser.USER_ID_KEY] = user_id
        # Get user from session
        elif CYMUser.USER_ID_KEY in request.session:
            user_id = request.session[CYMUser.USER_ID_KEY]
            try:
                request.cym_user = CYMUser.objects.get(id=user_id)
            except ObjectDoesNotExist:
                del request.session[CYMUser.USER_ID_KEY]
                request.cym_user = None
        # Not logged in
        else:
            request.cym_user = None


def needs_login(wrapped):
    @functools.wraps(wrapped)
    def wrapper(request, *args, **kwargs):
        if request.cym_user is None:
            return redirect(
                '%s?%s' % (reverse('login'),
                           urllib.parse.urlencode({'path': request.path})),
                permanent=False)
        return wrapped(request, *args, **kwargs)

    return wrapper


def make_login_link(user_id, path='/'):
    signer = Signer()
    token = signer.sign(str(user_id))
    token = b32encode(token.encode('ascii')).decode('ascii')
    return settings.URL_ROOT + path + '?token=' + token


# FIXME: debug
def send_mail(**kwargs):
    print("WOULD SEND EMAIL")
    for k, v in kwargs.items():
        print("    {0}: {1}".format(k, v))


def send_login_email(user, path='/'):
    link = make_login_link(user.id, path)

    send_mail(
        subject="Log in to Call Your mom",
        message="Someone requested a login link for call your mom. You "
                "can use the link below to log in:\n"
                "\n{0}\n\n"
                "If this wasn't you, feel free to ignore this "
                "message.".format(link),
        from_email=settings.EMAIL_FROM,
        recipient_list=[user.email],
    )


def send_register_email(user):
    link = make_login_link(user.id)

    send_mail(
        subject="Register for Call Your mom",
        message="Someone requested an account for call your mom using this "
                "email address. You can use the link below to log in:\n"
                "\n{0}\n\n"
                "If this wasn't you, feel free to ignore this "
                "message.".format(link),
        from_email=settings.EMAIL_FROM,
        recipient_list=[user.email],
    )
