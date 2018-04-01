from base64 import b32decode
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import Signer
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import functools
import urllib.parse

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
