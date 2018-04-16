from base64 import b32encode, b32decode
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.signing import Signer
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _
import functools
import logging
import urllib.parse

from website import settings
from .models import CYMUser


logger = logging.getLogger(__name__)


class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Use a token to log in
        if 'token' in request.GET:
            token = request.GET['token']
            token = b32decode(token.upper().encode('ascii')).decode('ascii')
            user_id = Signer().unsign(token)
            request.cym_user = CYMUser.objects.get(id=user_id)
            request.cym_user.last_login = timezone.now()
            request.cym_user.save()
            request.session[CYMUser.USER_ID_KEY] = user_id

            # Also set preferred language
            lang = request.cym_user.language
            translation.activate(lang)
            request.session[translation.LANGUAGE_SESSION_KEY] = lang

            # And preferred timezone
            timezone.activate(request.cym_user.timezone)

            # Redirect to destination without token
            return redirect(request.path)
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


def clear_login(request):
    request.session.pop(CYMUser.USER_ID_KEY, None)


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


class EmailRateLimit(RuntimeError):
    """Hit rate limit of emails.
    """


def email_rate_limit(user, now=None):
    if now is None:
        now = timezone.now()

    # Don't ever send more than one email every 5 minutes
    if user.last_login_email + datetime.timedelta(minutes=5) > now:
        logger.warning("Rate-limiting at 10 minutes")
        raise EmailRateLimit("Sent email less than 10 minutes ago")

    # If the user logged in since his last email, he can get a new one
    if user.last_login is not None and user.last_login > user.last_login_email:
        return

    # If user never completed registration, new email can be sent after 7 days
    if user.last_login is None:
        delay = datetime.timedelta(days=7)
        if user.last_login_email + delay > now:
            logger.warning("Rate-limiting at 7 days")
            raise EmailRateLimit("User never logged in and we sent email less "
                                 "than 7 days ago")
    # If the user did finish registering, new email can be sent after 1 day
    else:
        delay = datetime.timedelta(hours=23)
        if user.last_login_email + delay > now:
            logger.warning("Rate-limiting at 23 hours")
            raise EmailRateLimit("User didn't log in since last email and we "
                                 "sent email less than 23 hours ago")


def make_login_link(user_id, path='/'):
    signer = Signer()
    token = signer.sign(str(user_id))
    token = b32encode(token.encode('ascii')).decode('ascii')
    return settings.URL_ROOT + path + '?token=' + token


def send_login_email(user, path='/'):
    email_rate_limit(user)

    link = make_login_link(user.id, path)

    # We send the email in the user's preferred language, not the requester's
    cur_language = translation.get_language()
    try:
        translation.activate(user.language)
        send_mail(
            subject="Log in to Call Your mom",
            message="{0}\n\n{1}\n\n{2}".format(
                _("Someone requested a login link for Call Your Mom. You can "
                  "use the link below to log in:"),
                link,
                _("If this wasn't you, feel free to ignore this message."),
            ),
            html_message=render_to_string('call_your_mom/email_login.html', {
                'link': link,
            }),
            from_email=settings.EMAIL_FROM,
            recipient_list=[user.email],
        )
    finally:
        translation.activate(cur_language)


def send_register_email(user):
    email_rate_limit(user)

    link = make_login_link(user.id)

    # We send the email in the user's preferred language, not the requester's
    cur_language = translation.get_language()
    try:
        translation.activate(user.language)
        send_mail(
            subject="Register for Call Your mom",
            message="{0}\n\n{1}\n\n{2}".format(
                _("Someone requested an account for Call Your Mom using this "
                  "email address. You can use the link below to log in:"),
                link,
                _("If this wasn't you, feel free to ignore this message."),
            ),
            html_message=render_to_string(
                'call_your_mom/email_register.html',
                {'link': link}),
            from_email=settings.EMAIL_FROM,
            recipient_list=[user.email],
        )
    finally:
        translation.activate(cur_language)
