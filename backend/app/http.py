"""HTTP budgets are enforced on received bytes, independently of Content-Length."""
import asyncio
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 8*1024*1024


class BodyTooLarge(Exception):
    pass


def permitted_origin(request, config):
    if request.headers.get('sec-fetch-site') == 'cross-site':
        return False
    value = request.headers.get('origin')
    if value is None:
        return True  # Non-browser clients still need the existing custom write header.
    try:
        origin = urlsplit(value)
        valid = (len(value) <= 2048 and origin.scheme in ('http','https') and origin.hostname in config.allowed_hosts
                 and not origin.username and not origin.password and not origin.path
                 and not origin.query and not origin.fragment and origin.port != 0)
    except ValueError:
        return False
    return valid and (config.public_origin is None or value == config.public_origin)


class RequestBudgetMiddleware:
    def __init__(self, app, max_bytes=MAX_REQUEST_BYTES, timeout=10):
        self.app = app
        self.max_bytes = max_bytes
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', ()))
        if b'content-length' in headers:
            try:
                size = int(headers[b'content-length'])
                if size < 0:
                    raise ValueError()
            except ValueError:
                return await self.reject(scope, receive, send, 400, 'Некорректная длина запроса.')
            if size > self.max_bytes:
                return await self.reject(scope, receive, send, 413, 'Размер запроса превышает 8 МБ.')
        body = bytearray()
        try:
            async with asyncio.timeout(self.timeout):
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > self.max_bytes:
                        raise BodyTooLarge()
                    body.extend(chunk)
                    if not message.get('more_body', False):
                        break
        except TimeoutError:
            return await self.reject(scope, receive, send, 408, 'Время приёма запроса истекло.')
        except BodyTooLarge:
            return await self.reject(scope, receive, send, 413, 'Размер запроса превышает 8 МБ.')
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()

        await self.app(scope, replay, send)

    @staticmethod
    async def reject(scope, receive, send, status, detail):
        response = JSONResponse({'detail': detail}, status_code=status,
                                headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
        await response(scope, receive, send)
