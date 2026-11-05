from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.environment import get_allowed_hosts, get_bool, get_int, get_secret_key


class EnvironmentSettingsTests(SimpleTestCase):
    def test_boolean_environment_values_are_parsed(self):
        for value in ("1", "true", "YES", "on"):
            with self.subTest(value=value), patch.dict("os.environ", {"SETTING": value}):
                self.assertTrue(get_bool("SETTING", default=False))

        for value in ("0", "false", "NO", "off"):
            with self.subTest(value=value), patch.dict("os.environ", {"SETTING": value}):
                self.assertFalse(get_bool("SETTING", default=True))

    def test_invalid_boolean_value_is_rejected(self):
        with patch.dict("os.environ", {"SETTING": "sometimes"}):
            with self.assertRaises(ImproperlyConfigured):
                get_bool("SETTING", default=False)

    def test_secret_key_is_required(self):
        with patch.dict("os.environ", {"DJANGO_SECRET_KEY": "  "}):
            with self.assertRaises(ImproperlyConfigured):
                get_secret_key()

    def test_allowed_hosts_are_required_outside_debug(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                get_allowed_hosts(debug=False)

    def test_allowed_hosts_are_parsed_from_comma_separated_value(self):
        with patch.dict(
            "os.environ",
            {"DJANGO_ALLOWED_HOSTS": "example.com, api.example.com "},
        ):
            self.assertEqual(
                get_allowed_hosts(debug=False),
                ["example.com", "api.example.com"],
            )

    def test_integer_settings_are_validated(self):
        with patch.dict("os.environ", {"SETTING": "10"}):
            self.assertEqual(get_int("SETTING", default=5, minimum=1, maximum=30), 10)

        for value in ("not-a-number", "0", "31"):
            with self.subTest(value=value), patch.dict("os.environ", {"SETTING": value}):
                with self.assertRaises(ImproperlyConfigured):
                    get_int("SETTING", default=5, minimum=1, maximum=30)
