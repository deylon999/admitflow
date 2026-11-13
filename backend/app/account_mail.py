"""Account mail port and TLS-only SMTP. No runtime mock transport or secret logging."""
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from threading import BoundedSemaphore
from typing import Protocol
import smtplib
import ssl

from .account_security import credential_digest, normalize_email

_SEND_SLOTS = BoundedSemaphore(2)


class MailDeliveryError(RuntimeError):
    def __init__(self):
        super().__init__('Account mail delivery is unavailable.')


class RegistrationMailer(Protocol):
    available: bool

    def deliver_registration(self, email: str, verification_token: str | None) -> None: ...
    def deliver_verification(self, email: str, verification_token: str | None) -> None: ...
    def deliver_recovery(self, email: str, recovery_token: str | None) -> None: ...


class UnavailableRegistrationMailer:
    available = False

    def deliver_registration(self, email, verification_token): raise MailDeliveryError()
    def deliver_verification(self, email, verification_token): raise MailDeliveryError()
    def deliver_recovery(self, email, recovery_token): raise MailDeliveryError()


class SmtpAccountMailer:
    """One attempt per request, two concurrent sends per process, finite socket timeout.

    SMTP acceptance confirms the provider accepted DATA, not inbox delivery. Ignore
    QUIT failure after acceptance; retrying then could duplicate an accepted mail.
    """
    available = True

    def __init__(self, config):
        self.config = config

    def deliver_registration(self, email, verification_token):
        self._deliver(email, 'verify_email', verification_token)

    def deliver_verification(self, email, verification_token):
        self._deliver(email, 'verify_email', verification_token)

    def deliver_recovery(self, email, recovery_token):
        self._deliver(email, 'reset_password', recovery_token)

    def _deliver(self, email, purpose, token):
        recipient = normalize_email(email)
        message = EmailMessage()
        message['From'] = normalize_email(self.config.smtp_from)
        message['To'] = recipient
        message['Subject'] = 'AdmitFlow: запрос для аккаунта'
        message['Date'] = formatdate(localtime=False)
        message['Message-ID'] = make_msgid(domain=str(message['From']).split('@', 1)[1])
        if token is None:
            content = ('Получен запрос для этого адреса в AdmitFlow. Если операция доступна, '
                       'используйте ранее полученную ссылку или запросите новую в приложении. '
                       'Если вы не отправляли запрос, проигнорируйте это письмо.')
        else:
            credential_digest(purpose, token)  # Validate shape and separate allowed purposes.
            path = '/auth/verify' if purpose == 'verify_email' else '/auth/reset'
            link = self.config.public_origin+path+'#token='+token
            content = (('Подтвердите email. Ссылка действует24 часа.' if purpose == 'verify_email'
                        else 'Установите новый пароль. Ссылка действует30 минут.')
                       +'\n\n'+link+'\n\nНовый запрос делает предыдущую ссылку недействительной. '
                       'Если вы не отправляли запрос, не переходите по ссылке и проигнорируйте письмо.')
        # ASCII wire representation also works with relays lacking 8BITMIME.
        message.set_content(content, cte='quoted-printable')
        if not _SEND_SLOTS.acquire(blocking=False):
            raise MailDeliveryError()
        client = None
        try:
            context = ssl.create_default_context()
            options = dict(timeout=self.config.smtp_timeout_seconds)
            if self.config.smtp_security == 'ssl':
                client = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port, context=context, **options)
            else:
                client = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, **options)
                client.ehlo()
                client.starttls(context=context)  # Missing STARTTLS fails closed; never downgrade.
            client.ehlo()
            client.login(self.config.smtp_username, self.config.smtp_password)
            refused = client.send_message(message, from_addr=message['From'], to_addrs=[recipient])
            if refused:
                raise MailDeliveryError()
        except Exception:
            raise MailDeliveryError() from None
        finally:
            if client is not None:
                try:
                    client.quit()
                except Exception:
                    try: client.close()
                    except Exception: pass
            _SEND_SLOTS.release()


def configured_mailer(config):
    return SmtpAccountMailer(config) if config.smtp_host else UnavailableRegistrationMailer()
