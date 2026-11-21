"""Explicit real-transport smoke check. Does not create users or action tokens."""
import argparse
import os

from .auth.account_mail import MailDeliveryError, configured_mailer
from .auth.account_security import InvalidAccountInput, normalize_email
from .config import Settings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--send', action='store_true', help='Send one real generic account notice to AUTH_TEST_EMAIL')
    args = parser.parse_args(argv)
    try:
        config = Settings.from_env()
        if not config.auth_enabled or not config.secure_cookie or not config.smtp_host:
            raise ValueError()
        mailer = configured_mailer(config)
        recipient = normalize_email(os.getenv('AUTH_TEST_EMAIL')) if args.send else None
    except (RuntimeError, ValueError, InvalidAccountInput):
        print('SMTP check configuration invalid: require auth, secure cookies, HTTPS origin, SMTP and (with --send) controlled AUTH_TEST_EMAIL.')
        return 2
    if not args.send:
        print('Configuration valid. No network connection or mail attempted. Run --send from the backend network for a real smoke check.')
        return 0
    try:
        mailer.deliver_verification(recipient, None)
    except MailDeliveryError:
        print('SMTP submission failed. No delivery is claimed; check provider/network configuration privately.')
        return 1
    print('SMTP provider accepted one account notice. Confirm receipt in the controlled inbox; this is not proof of inbox delivery or an auth lifecycle test.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
