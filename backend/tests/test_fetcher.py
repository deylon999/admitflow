import hashlib
import ssl
from unittest.mock import Mock

import pytest

from app.sources.fetcher import FetchError, Fetcher, FetchPolicy, HTTPSReader, PinnedHTTPSConnection, RawResponse, retry_delay

POLICY = FetchPolicy(frozenset({'lists.example.org'}), max_bytes=1024)
GOOD = RawResponse(200, {'content-type': 'text/html; charset=utf-8'}, b'<table>synthetic</table>')


class Reader:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def read(self, url, address, policy):
        self.calls.append((url, address))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def fetcher(reader, resolver=lambda _: ['93.184.216.34']):
    return Fetcher(POLICY, reader=reader, resolver=resolver)


def test_success_pins_resolution_and_returns_provenance_without_logging_body():
    resolver = Mock(return_value=['93.184.216.34'])
    reader = Reader(GOOD)
    result = fetcher(reader, resolver).fetch('https://lists.example.org/list?group=1')
    assert reader.calls == [('https://lists.example.org/list?group=1', '93.184.216.34')]
    resolver.assert_called_once_with('lists.example.org')
    assert result.payload_hash == hashlib.sha256(GOOD.body).hexdigest()
    assert result.fetched_at.tzinfo is not None
    assert result.charset == 'utf-8'
    assert 'group=1' not in repr(result) and 'synthetic' not in repr(result)


@pytest.mark.parametrize('url', [
    'http://lists.example.org', 'file:///etc/passwd',
    'https://lists.example.org:8443/', 'https://user:password@lists.example.org/',
    'https://lists.example.org.evil.test/', 'https://localhost/',
    'https://127.0.0.1/', 'https://lists.example.org/#fragment',
    'https://lists.example.org/\r\nheader', '/relative', None,
])
def test_invalid_or_unapproved_urls_never_reach_dns(url):
    resolver = Mock()
    with pytest.raises(FetchError):
        fetcher(Reader(), resolver).fetch(url)
    resolver.assert_not_called()


@pytest.mark.parametrize('addresses', [
    ['127.0.0.1'], ['10.0.0.1'], ['169.254.169.254'], ['::1'],
    ['::ffff:127.0.0.1'], ['224.0.0.1'], ['ff02::1'], ['fec0::1'],
    ['93.184.216.34', '192.168.1.1'], [],
])
def test_dns_private_or_mixed_answers_are_rejected(addresses):
    reader = Reader()
    with pytest.raises(FetchError, match='non_public_address'):
        fetcher(reader, lambda _: addresses).fetch('https://lists.example.org')
    assert reader.calls == []


def test_redirect_is_validated_before_the_second_request():
    reader = Reader(RawResponse(302, {'location': 'http://127.0.0.1/private'}, b''))
    with pytest.raises(FetchError):
        fetcher(reader).fetch('https://lists.example.org')
    assert len(reader.calls) == 1


def test_same_domain_redirect_resolves_again_and_stops_rebinding():
    reader = Reader(RawResponse(302, {'location': '/next'}, b''))
    resolver = Mock(side_effect=[['93.184.216.34'], ['127.0.0.1']])
    with pytest.raises(FetchError, match='non_public_address'):
        fetcher(reader, resolver).fetch('https://lists.example.org')
    assert len(reader.calls) == 1


def test_redirect_loop_is_bounded():
    reader = Reader(*(RawResponse(302, {'location': '/next'}, b'') for _ in range(4)))
    with pytest.raises(FetchError, match='too_many_redirects'):
        fetcher(reader).fetch('https://lists.example.org')
    assert len(reader.calls) == 4


@pytest.mark.parametrize('response,code', [
    (RawResponse(403, {}, b''), 'access_denied'),
    (RawResponse(401, {}, b''), 'access_denied'),
    (RawResponse(500, {}, b''), 'http_error'),
    (RawResponse(200, {'content-type': 'image/png'}, b'x'), 'unsupported_content_type'),
    (RawResponse(200, {'content-type': 'text/html'}, b''), 'empty_response'),
    (RawResponse(200, {'content-type': 'text/html'}, b'x' * 1025), 'response_too_large'),
    (RawResponse(200, {'cf-mitigated': 'challenge'}, b'x'), 'access_challenge'),
    (RawResponse(200, {'content-type': 'text/html', 'content-encoding': 'gzip'}, b'x'), 'unsupported_encoding'),
])
def test_failed_responses_are_not_returned_as_source_data(response, code):
    with pytest.raises(FetchError, match=code):
        fetcher(Reader(response)).fetch('https://lists.example.org')


def test_retry_after_and_transport_errors_are_safe_and_bounded():
    with pytest.raises(FetchError) as error:
        fetcher(Reader(RawResponse(429, {'retry-after': '120'}, b''))).fetch('https://lists.example.org')
    assert error.value.retry_after == 120
    assert retry_delay('999999999') == 86400
    assert retry_delay('invalid') == 60
    for failure, code in [(TimeoutError('secret-url'), 'timeout'), (ssl.SSLError('secret-url'), 'tls_error'), (OSError('secret-url'), 'network_error')]:
        with pytest.raises(FetchError, match=code) as error:
            fetcher(Reader(failure)).fetch('https://lists.example.org')
        assert 'secret-url' not in str(error.value)


def test_tls_connects_to_pinned_ip_but_checks_original_hostname(monkeypatch):
    raw_socket = Mock()
    tls_context = Mock()
    connect = Mock(return_value=raw_socket)
    monkeypatch.setattr('socket.create_connection', connect)
    monkeypatch.setattr('ssl.create_default_context', lambda: tls_context)
    connection = PinnedHTTPSConnection('lists.example.org', '93.184.216.34', 10)
    connection.connect()
    connect.assert_called_once_with(('93.184.216.34', 443), timeout=10)
    tls_context.wrap_socket.assert_called_once_with(raw_socket, server_hostname='lists.example.org')


def test_stream_reader_stops_at_size_limit(monkeypatch):
    connection = Mock()
    response = connection.getresponse.return_value
    response.status = 200
    response.getheaders.return_value = [('content-type', 'text/html')]
    response.read.side_effect = [b'x' * 1024, b'y']
    monkeypatch.setattr('app.sources.fetcher.PinnedHTTPSConnection', lambda *args: connection)
    with pytest.raises(FetchError, match='response_too_large'):
        HTTPSReader().read('https://lists.example.org', '93.184.216.34', POLICY)
    connection.close.assert_called_once()
