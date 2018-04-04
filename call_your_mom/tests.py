from django.test import TestCase

from . import views


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
