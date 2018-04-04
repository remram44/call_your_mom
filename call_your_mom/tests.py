from django.test import TestCase
from django.urls import reverse, resolve
import contextlib
import urllib.parse

from . import views
from .models import CYMUser


def parse_url(path):
    parsed = urllib.parse.urlsplit(path)
    return resolve(parsed.path), urllib.parse.parse_qs(parsed.query)


class LogInTestCase(TestCase):
    def setUp(self):
        self.__session = self.client.session

    @contextlib.contextmanager
    def logged_in(self, user_id=1):
        self.__session[CYMUser.USER_ID_KEY] = 1
        self.__session.save()
        try:
            yield
        finally:
            self.__session.pop(CYMUser.USER_ID_KEY, None)
            self.__session.save()


class TimezonesTestCase(TestCase):
    def test_timezone_list(self):
        # Check reasonable number
        self.assertGreater(len(views._timezones), 200)
        self.assertLess(len(views._timezones), 2000)

        # Check some timezones
        tz = [tz for tz in views._timezones if tz[0] == 'Europe/Paris']
        self.assertEqual(tz, [('Europe/Paris', '+01:00')])
        tz = [tz for tz in views._timezones if tz[0] == 'America/New_York']
        self.assertEqual(tz, [('America/New_York', '-05:00')])


class AuthCase(LogInTestCase):
    fixtures = ['test.json']

    def test_landing(self):
        # Not logged in - index gets you to /landing
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('landing')))

        # Logged in - index gets you to /profile
        with self.logged_in():
            response = self.client.get(reverse('index'))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('profile')))


class AckTestCase(LogInTestCase):
    fixtures = ['test.json']

    def test_view(self):
        # Not logged in
        response = self.client.get(reverse('ack_task', args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(parse_url(response.url)[0].url_name, 'login')

        with self.logged_in():
            response = self.client.get(reverse('ack_task', args=[1]))
            self.assertEqual(response.status_code, 404)
            response = self.client.get(reverse('ack_task', args=[2]))
            self.assertEqual(response.status_code, 200)
