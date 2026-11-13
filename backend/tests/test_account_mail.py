import smtplib
import ssl
from urllib.parse import urlsplit

import pytest

from app import account_mail
from app.account_mail import MailDeliveryError, SmtpAccountMailer, configured_mailer
from app.account_security import new_token
from app.config import Settings


BASE = dict(public_origin='https://example.org', allowed_hosts=('example.org',), smtp_host='smtp.example.net',
            smtp_username='private-smtp-user', smtp_password='private-smtp-password', smtp_from='Sender@mailer.example.net')


class FakeSMTP:
    def __init__(self, *, implicit=False, failure=None):
        self.events, self.messages = [], []
        self.tls, self.failure = implicit, failure
        self.context = None
    def ehlo(self): self.events.append('ehlo')
    def starttls(self, *, context):
        self.events.append('tls'); self.context = context
        if self.failure == 'tls': raise smtplib.SMTPNotSupportedError('private provider detail')
        if self.failure == 'cert': raise ssl.SSLCertVerificationError('private certificate detail')
        self.tls = True
    def login(self, user, password):
        assert self.tls
        self.events.append('login')
        if self.failure == 'auth': raise smtplib.SMTPAuthenticationError(535, b'private credentials rejected')
    def send_message(self, message, **kwargs):
        self.events.append('send'); self.messages.append((message, kwargs))
        if self.failure == 'send': raise TimeoutError('private provider detail')
        return {'person@example.org': (550, b'private refused')} if self.failure == 'refused' else {}
    def quit(self):
        self.events.append('quit')
        if self.failure == 'quit': raise smtplib.SMTPServerDisconnected('private provider detail')
    def close(self): self.events.append('close')


@pytest.mark.parametrize('mode', ['starttls', 'ssl'])
@pytest.mark.parametrize('operation,path', [('deliver_registration','/auth/verify'), ('deliver_verification','/auth/verify'), ('deliver_recovery','/auth/reset')])
def test_smtp_tls_and_fixed_fragment_links(monkeypatch, mode, operation, path):
    instances, calls = [], []
    def connect(*args, **kwargs):
        calls.append((args, kwargs)); client = FakeSMTP(implicit=mode=='ssl'); instances.append(client); return client
    monkeypatch.setattr(account_mail.smtplib, 'SMTP' if mode=='starttls' else 'SMTP_SSL', connect)
    config = Settings(**(BASE | dict(smtp_security=mode, smtp_port=465 if mode=='ssl' else 587)))
    token = new_token()
    getattr(configured_mailer(config), operation)('Person@Example.ORG', token)
    client = instances[0]
    context = client.context if mode=='starttls' else calls[0][1]['context']
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    assert calls[0][1]['timeout'] == 5
    assert client.events.index('send') > client.events.index('login')
    if mode=='starttls': assert client.events == ['ehlo','tls','ehlo','login','send','quit']
    message, envelope = client.messages[0]
    assert str(message['Message-ID']).endswith('@mailer.example.net>')
    assert message.as_bytes().isascii() and message.get_content_charset() == 'utf-8'
    text = message.get_content(); link = next(line for line in text.splitlines() if line.startswith('https://'))
    parts = urlsplit(link)
    assert parts.netloc == 'example.org' and parts.path == path and not parts.query and parts.fragment == 'token='+token
    assert envelope == dict(from_addr='sender@mailer.example.net', to_addrs=['person@example.org'])
    assert BASE['smtp_password'] not in text and BASE['smtp_username'] not in text
    assert 'не переходите' in text


@pytest.mark.parametrize('failure', ['connect', 'tls', 'cert', 'auth', 'send', 'refused'])
def test_smtp_failure_is_explicit_sanitized_and_not_retried(monkeypatch, failure, caplog):
    clients = []
    def connect(*args, **kwargs):
        client = FakeSMTP(failure=failure); clients.append(client)
        if failure == 'connect': raise TimeoutError('private connect detail')
        return client
    monkeypatch.setattr(account_mail.smtplib, 'SMTP', connect)
    with pytest.raises(MailDeliveryError) as error:
        SmtpAccountMailer(Settings(**BASE)).deliver_recovery('person@example.org', new_token())
    assert len(clients) == 1 and clients[0].events.count('send') <= 1
    assert 'private' not in str(error.value) and 'private' not in caplog.text
    # Capacity is released even after rejection/connection failure.
    assert account_mail._SEND_SLOTS.acquire(False); account_mail._SEND_SLOTS.release()


def test_quit_failure_after_acceptance_does_not_duplicate_or_claim_send_failure(monkeypatch):
    client = FakeSMTP(failure='quit')
    monkeypatch.setattr(account_mail.smtplib, 'SMTP', lambda *args, **kwargs: client)
    SmtpAccountMailer(Settings(**BASE)).deliver_registration('person@example.org', new_token())
    assert client.events.count('send') == 1 and client.events[-1] == 'close'


def test_generic_notice_and_capacity_limit_are_real_transport_operations(monkeypatch):
    client = FakeSMTP(); calls = []
    def connect(*args, **kwargs): calls.append(True); return client
    monkeypatch.setattr(account_mail.smtplib, 'SMTP', connect)
    mailer = configured_mailer(Settings(**BASE))
    mailer.deliver_recovery('person@example.org', None)
    assert len(client.messages) == 1 and '#token=' not in client.messages[0][0].get_content()
    assert account_mail._SEND_SLOTS.acquire(False); assert account_mail._SEND_SLOTS.acquire(False)
    try:
        with pytest.raises(MailDeliveryError): mailer.deliver_recovery('person@example.org', new_token())
    finally:
        account_mail._SEND_SLOTS.release(); account_mail._SEND_SLOTS.release()
    assert len(calls) == 1


@pytest.mark.parametrize('patch', [dict(smtp_host='https://smtp.example.net'), dict(smtp_host='bad\r\nhost'),
    dict(smtp_username=None), dict(smtp_password=None), dict(smtp_from='sender@example.org\r\nBcc:x@example.org'),
    dict(smtp_security='plain'), dict(smtp_port=0), dict(smtp_port=True), dict(smtp_timeout_seconds=0),
    dict(smtp_timeout_seconds=11), dict(public_origin='http://example.org')])
def test_unsafe_or_partial_smtp_config_fails_closed(patch):
    with pytest.raises(RuntimeError): Settings(**(BASE | patch))


def test_absent_provider_and_secret_free_config_repr(monkeypatch):
    mailer = configured_mailer(Settings())
    assert not mailer.available
    with pytest.raises(MailDeliveryError): mailer.deliver_verification('person@example.org', new_token())
    config = Settings(**BASE)
    assert BASE['smtp_password'] not in repr(config) and BASE['smtp_username'] not in repr(config)
    for key,value in {'SMTP_HOST':BASE['smtp_host'], 'SMTP_USERNAME':BASE['smtp_username'],
                      'SMTP_PASSWORD':BASE['smtp_password'], 'SMTP_FROM':BASE['smtp_from'],
                      'SMTP_SECURITY':'ssl', 'PUBLIC_ORIGIN':'https://example.org', 'ALLOWED_HOSTS':'example.org'}.items():
        monkeypatch.setenv(key,value)
    assert Settings.from_env().smtp_port == 465
    monkeypatch.setenv('SMTP_PORT','not-an-integer')
    with pytest.raises(RuntimeError): Settings.from_env()
