from app import smtp_check
from app.account_mail import MailDeliveryError
from app.config import Settings
from test_account_mail import BASE


def setup(monkeypatch):
    config = Settings(**BASE, auth_enabled=True, auth_rate_key='k'*32, secure_cookie=True)
    monkeypatch.setattr(smtp_check.Settings, 'from_env', lambda: config)
    monkeypatch.setenv('AUTH_TEST_EMAIL', 'controlled@example.org')


def test_configuration_does_not_send(monkeypatch):
    setup(monkeypatch)
    monkeypatch.setattr(smtp_check, 'configured_mailer', lambda _: object())
    assert smtp_check.main([]) == 0


def test_explicit_send_and_sanitized_failure(monkeypatch, capsys):
    setup(monkeypatch)
    class Transport:
        def deliver_verification(self, email, token):
            assert email == 'controlled@example.org' and token is None
            raise MailDeliveryError()
    monkeypatch.setattr(smtp_check, 'configured_mailer', lambda _: Transport())
    assert smtp_check.main(['--send']) == 1
    text = capsys.readouterr().out
    assert 'accepted' not in text and 'controlled@' not in text and BASE['smtp_password'] not in text


def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(smtp_check.Settings, 'from_env', lambda: Settings())
    assert smtp_check.main(['--send']) == 2
