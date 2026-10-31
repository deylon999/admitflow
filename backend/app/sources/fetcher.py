"""Bounded HTTPS download with allowlisted domains and a pinned public IP."""
import hashlib
import http.client
import ipaddress
import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from email.message import Message
from urllib.parse import urljoin, urlsplit, urlunsplit


class FetchError(Exception):
    def __init__(self, code, *, retry_after=None):
        super().__init__(code)
        self.code = code
        self.retry_after = retry_after


@dataclass(frozen=True)
class FetchPolicy:
    domains: frozenset[str]
    max_bytes: int = 5 * 1024 * 1024
    timeout: float = 10
    max_redirects: int = 3
    content_types: frozenset[str] = frozenset({'text/html', 'application/json', 'text/csv', 'text/plain'})


@dataclass(frozen=True)
class RawResponse:
    status: int
    headers: dict[str, str]
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class FetchResult:
    url: str = field(repr=False)
    body: bytes = field(repr=False)
    content_type: str
    payload_hash: str
    fetched_at: datetime
    charset: str | None = None


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname, address, timeout):
        super().__init__(hostname, port=443, timeout=timeout)
        self.address = address

    def connect(self):
        connection = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            # TLS still validates the official hostname, not the resolved IP.
            context = ssl.create_default_context()
            context.set_alpn_protocols(['http/1.1'])
            self.sock = context.wrap_socket(connection, server_hostname=self.host)
        except Exception:
            connection.close()
            raise


def resolve(hostname):
    return list(dict.fromkeys(item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)))


class HTTPSReader:
    def read(self, url, address, policy):
        parsed = urlsplit(url)
        connection = PinnedHTTPSConnection(parsed.hostname, address, policy.timeout)
        deadline = time.monotonic() + policy.timeout
        try:
            path = urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
            connection.request('GET', path, headers={'User-Agent': 'AdmitFlow/0.2', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            headers = {key.lower(): value for key, value in response.getheaders()}
            if response.status != 200:
                return RawResponse(response.status, headers, b'')
            if headers.get('content-encoding', 'identity').lower() != 'identity':
                raise FetchError('unsupported_encoding')
            if 'content-length' in headers:
                try:
                    size = int(headers['content-length'])
                except ValueError:
                    raise FetchError('invalid_headers') from None
                if size < 0 or size > policy.max_bytes:
                    raise FetchError('response_too_large')
            chunks, size = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise FetchError('timeout', retry_after=60)
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read(min(65536, policy.max_bytes - size + 1))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > policy.max_bytes:
                    raise FetchError('response_too_large')
            return RawResponse(response.status, headers, b''.join(chunks))
        finally:
            connection.close()


def retry_delay(value):
    try:
        seconds = int(value)
    except (ValueError, TypeError):
        try:
            seconds = int((parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            seconds = 60
    return min(86400, max(30, seconds))


class Fetcher:
    def __init__(self, policy, *, resolver=resolve, reader=None):
        if not policy.domains or policy.max_bytes <= 0 or policy.timeout <= 0 or not 0 <= policy.max_redirects <= 5:
            raise ValueError('Invalid fetch policy')
        self.policy, self.resolver, self.reader = policy, resolver, reader or HTTPSReader()

    def _target(self, value):
        if not isinstance(value, str) or len(value) > 4096 or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise FetchError('invalid_url')
        try:
            parsed = urlsplit(value)
            hostname = (parsed.hostname or '').encode('idna').decode('ascii').lower()
            port = parsed.port
        except (ValueError, UnicodeError):
            raise FetchError('invalid_url') from None
        if parsed.scheme != 'https' or port not in (None, 443) or parsed.username or parsed.password or parsed.fragment:
            raise FetchError('invalid_url')
        if hostname not in self.policy.domains:
            raise FetchError('domain_not_allowed')
        try:
            addresses = self.resolver(hostname)
            ips = [ipaddress.ip_address(address) for address in addresses]
            if not ips or any(not ip.is_global or ip.is_multicast or ip.is_reserved or getattr(ip, 'is_site_local', False) for ip in ips):
                raise FetchError('non_public_address')
        except (OSError, ValueError):
            raise FetchError('dns_unavailable', retry_after=60) from None
        return urlunsplit(('https', hostname, parsed.path or '/', parsed.query, '')), addresses[0]

    def fetch(self, url):
        for hop in range(self.policy.max_redirects + 1):
            target, address = self._target(url)
            try:
                response = self.reader.read(target, address, self.policy)
            except (TimeoutError, socket.timeout):
                raise FetchError('timeout', retry_after=60) from None
            except ssl.SSLError:
                raise FetchError('tls_error', retry_after=300) from None
            except (OSError, http.client.HTTPException):
                raise FetchError('network_error', retry_after=60) from None
            headers = {key.lower(): value for key, value in response.headers.items()}
            if response.status in (301, 302, 303, 307, 308):
                if hop >= self.policy.max_redirects:
                    raise FetchError('too_many_redirects')
                location = headers.get('location')
                if not location:
                    raise FetchError('invalid_redirect')
                url = urljoin(target, location)
                continue
            if response.status in (401, 403):
                raise FetchError('access_denied')
            if response.status == 429:
                raise FetchError('rate_limited', retry_after=retry_delay(headers.get('retry-after')))
            if response.status != 200:
                raise FetchError('http_error', retry_after=retry_delay(headers.get('retry-after')) if response.status >= 500 else None)
            if headers.get('cf-mitigated') == 'challenge':
                raise FetchError('access_challenge')
            if headers.get('content-encoding', 'identity').lower() != 'identity':
                raise FetchError('unsupported_encoding')
            content_type = headers.get('content-type', '').split(';')[0].strip().lower()
            if content_type not in self.policy.content_types:
                raise FetchError('unsupported_content_type')
            if not response.body:
                raise FetchError('empty_response')
            if len(response.body) > self.policy.max_bytes:
                raise FetchError('response_too_large')
            metadata = Message()
            metadata['content-type'] = headers['content-type']
            return FetchResult(target, response.body, content_type, hashlib.sha256(response.body).hexdigest(), datetime.now(timezone.utc), metadata.get_content_charset())
        raise FetchError('too_many_redirects')
