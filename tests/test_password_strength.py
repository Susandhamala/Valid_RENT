"""Tests: password strength validation on registration."""
import pytest
from tests.conftest import _login


def _register_raw(client, password, email='pwtest@test.com'):
    return client.post('/auth/register', data={
        'full_name': 'PW Test',
        'email': email,
        'phone': '9800000000',
        'role': 'tenant',
        'password': password,
        'confirm_password': password,
    }, follow_redirects=True)


class TestPasswordStrength:
    def test_short_password_rejected(self, client):
        r = _register_raw(client, 'Ab1!xxx')
        assert r.status_code == 200
        assert b'8 characters' in r.data or b'characters' in r.data

    def test_common_password_rejected(self, client):
        r = _register_raw(client, 'password123')
        assert r.status_code == 200
        assert b'too common' in r.data or b'common' in r.data

    def test_password_missing_uppercase_rejected(self, client):
        r = _register_raw(client, 'validr3nt!')
        assert r.status_code == 200
        assert b'uppercase' in r.data

    def test_password_missing_lowercase_rejected(self, client):
        r = _register_raw(client, 'VALIDR3NT!')
        assert r.status_code == 200
        assert b'lowercase' in r.data

    def test_password_missing_digit_rejected(self, client):
        r = _register_raw(client, 'ValidRent!')
        assert r.status_code == 200
        assert b'number' in r.data or b'digit' in r.data

    def test_password_missing_special_char_rejected(self, client):
        r = _register_raw(client, 'ValidR3nt')
        assert r.status_code == 200
        assert b'special' in r.data

    def test_strong_password_accepted(self, client):
        r = _register_raw(client, 'ValidR3nt!')
        assert r.status_code == 200
        assert b'8 characters' not in r.data
        assert b'uppercase' not in r.data
        assert b'too common' not in r.data
