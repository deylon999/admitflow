import pytest
from argon2 import extract_parameters, PasswordHasher
from argon2.low_level import Type

from app import account_security as security

PASSWORD = 'A sufficiently long passphrase!'


@pytest.mark.parametrize('email,expected', [
    ('  PERSON+tag@Example.ORG  ', 'person+tag@example.org'),
    ('first.last@xn--e1afmkfd.xn--p1ai', 'first.last@xn--e1afmkfd.xn--p1ai'),
])
def test_email_identity_policy(email, expected):
    assert security.normalize_email(email) == expected


@pytest.mark.parametrize('email', ['x', 'x@@example.org', '.x@example.org', 'x.@example.org',
    'x..y@example.org', 'x@-example.org', 'x@example-.org', 'x@localhost',
    'x@127.0.0.1', 'x@пример.рф', 'x\n@example.org', 'a'*65+'@example.org',
    '"quoted"@example.org', 'a@'+'b'*64+'.org', None, 'a'*321])
def test_invalid_email_does_not_echo_input(email):
    with pytest.raises(security.InvalidAccountInput, match='Некорректный email.'):
        security.normalize_email(email)


@pytest.mark.parametrize('password', ['short', '', 'password123456789', '123456789012345',
    'a'*129, 'a'*20+'\0', 'a'*20+'\ud800', None])
def test_password_policy_rejects_without_echo(password):
    with pytest.raises(security.InvalidAccountInput) as error:
        security.hash_password(password)
    if isinstance(password, str) and password:
        assert password not in str(error.value)


def test_argon2id_unique_salts_and_full_password_verification():
    first = security.hash_password(PASSWORD)
    second = security.hash_password(PASSWORD)
    params = extract_parameters(first)
    assert params.type == Type.ID
    assert (params.memory_cost, params.time_cost, params.parallelism, params.salt_len, params.hash_len) == (65536, 3, 4, 16, 32)
    assert first != second and PASSWORD not in first
    assert security.verify_password(PASSWORD, first) == security.PasswordCheck(True, False)
    assert not security.verify_password(PASSWORD+'wrong', first).valid
    assert not security.verify_password(PASSWORD, None).valid
    assert not security.verify_password(PASSWORD, 'malformed').valid
    # More expensive historical parameters prove rehash signalling without weakening tests.
    alternate = PasswordHasher(memory_cost=65536, time_cost=4, parallelism=4).hash(PASSWORD)
    assert security.verify_password(PASSWORD, alternate) == security.PasswordCheck(True, True)


@pytest.mark.parametrize('password', [' я люблю длинные парольные фразы ', '🦊'*128, 'a'*15, 'a'*128])
def test_unicode_whitespace_and_boundaries_preserved(password):
    encoded = security.hash_password(password)
    assert security.verify_password(password, encoded).valid
    if password != password.strip():
        assert not security.verify_password(password.strip(), encoded).valid


def test_hash_capacity_is_bounded_and_recovers():
    assert security._HASH_SLOTS.acquire(False)
    assert security._HASH_SLOTS.acquire(False)
    try:
        with pytest.raises(security.PasswordCapacityError): security.hash_password(PASSWORD)
        with pytest.raises(security.PasswordCapacityError): security.verify_password(PASSWORD, None)
    finally:
        security._HASH_SLOTS.release(); security._HASH_SLOTS.release()
    assert security.verify_password(PASSWORD, security.hash_password(PASSWORD)).valid


def test_tokens_are_random_purpose_separated_and_never_echoed():
    tokens = {security.new_token() for _ in range(100)}
    assert len(tokens) == 100
    token = tokens.pop()
    hashes = {security.credential_digest(p, token) for p in security._PURPOSES}
    assert len(hashes) == len(security._PURPOSES)
    assert all(len(digest) == 64 and token not in digest for digest in hashes)
    for invalid in ['x'*42, 'x'*44, '!'*43, None]:
        with pytest.raises(security.InvalidAccountInput): security.credential_digest('refresh', invalid)
    with pytest.raises(security.InvalidAccountInput): security.credential_digest('guest', token)
