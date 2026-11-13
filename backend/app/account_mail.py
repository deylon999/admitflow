"""Delivery boundary. Real SMTP/resend/confirmation are implemented in PR4.

No transport is selected via a test-mode environment variable. An unavailable
transport fails globally before user lookup; production never pretends to send.
"""
from typing import Protocol


class RegistrationMailer(Protocol):
    available: bool

    def deliver_registration(self, email: str, verification_token: str | None) -> None:
        """Confirm delivery acceptance or raise.

        A token means a new unverified account; None means send a generic account
        notice instead. Invoke for both cases to avoid a provider-error oracle.
        Never log arguments. Production link uses fixed configured PUBLIC_ORIGIN.
        """
        ...


class UnavailableRegistrationMailer:
    available = False

    def deliver_registration(self, email, verification_token):
        raise RuntimeError('Registration delivery is unavailable.')
