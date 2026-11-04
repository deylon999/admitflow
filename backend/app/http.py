"""HTTP budgets are enforced on received bytes, independently of Content-Length."""
import asyncio
import json
import logging
import math
import time
from urllib.parse import urlsplit
from uuid import uuid4

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 8*1024*1024
DEFAULT_REQUEST_BYTES = 64*1024
LARGE_BODY_PATHS = frozenset({'/api/v1/import'})


class BodyTooLarge(Exception):
    pass


def validate_json_document(body):
    depth, quoted, escaped = 0, False, False
    for byte in body:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 64:
                raise ValueError('json_depth')
        elif byte in (93, 125):
            depth -= 1
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('nonfinite_json')
        return result
    def constant(_):
        raise ValueError('nonfinite_json')
    try:
        json.loads(body, object_pairs_hook=pairs, parse_float=number, parse_constant=constant)
    except json.JSONDecodeError:
        pass  # Preserve FastAPI's normal malformed-document validation response.


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
    def __init__(self, app, max_bytes=MAX_REQUEST_BYTES, timeout=10, default_bytes=DEFAULT_REQUEST_BYTES):
        self.app = app
        self.max_bytes = max_bytes
        self.default_bytes = default_bytes
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        pairs = scope.get('headers', ())
        headers = dict(pairs)
        names = [name.lower() for name,_ in pairs]
        if names.count(b'content-type') > 1 or names.count(b'content-length') > 1:
            # Middleware and framework could otherwise read different values of the same header.
            return await self.reject(scope, receive, send, 400, 'Запрос содержит неоднозначные заголовки.')
        limit = self.max_bytes if scope.get('path') in LARGE_BODY_PATHS else min(self.max_bytes, self.default_bytes)
        too_large = f'Размер запроса превышает {limit//(1024*1024)} МБ.' if limit >= 1024*1024 else f'Размер запроса превышает {limit//1024} КБ.'
        if b'content-length' in headers:
            try:
                size = int(headers[b'content-length'])
                if size < 0:
                    raise ValueError()
            except ValueError:
                return await self.reject(scope, receive, send, 400, 'Некорректная длина запроса.')
            if size > limit:
                return await self.reject(scope, receive, send, 413, too_large)
        body = bytearray()
        try:
            async with asyncio.timeout(self.timeout):
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > limit:
                        raise BodyTooLarge()
                    body.extend(chunk)
                    if not message.get('more_body', False):
                        break
        except TimeoutError:
            return await self.reject(scope, receive, send, 408, 'Время приёма запроса истекло.')
        except BodyTooLarge:
            return await self.reject(scope, receive, send, 413, too_large)
        content_type = headers.get(b'content-type', b'').split(b';')[0].strip().lower()
        json_body = not content_type or content_type == b'application/json' or (content_type.startswith(b'application/') and content_type.endswith(b'+json'))
        if body and json_body:
            try:
                if len(body) > self.default_bytes:
                    # A large document must not stall every other request on the event loop.
                    await asyncio.to_thread(validate_json_document, bytes(body))
                else:
                    validate_json_document(body)
            except (ValueError, RecursionError):
                return await self.reject(scope, receive, send, 400, 'JSON содержит неоднозначные значения или превышает допустимую вложенность.')
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


class RequestDiagnosticsMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('admitflow.http')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers and not logging.getLogger().handlers:
            self.logger.addHandler(logging.StreamHandler())

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        start = time.perf_counter()
        status = 500
        started = False

        async def measured_send(message):
            nonlocal status, started
            if message['type'] == 'http.response.start':
                started = True
                status = message['status']
                replaced = {b'x-request-id',b'cache-control',b'x-content-type-options'}
                headers = [(key,value) for key,value in message.get('headers',[]) if key.lower() not in replaced]
                headers.extend([(b'x-request-id',request_id.encode()),(b'cache-control',b'no-store'),(b'x-content-type-options',b'nosniff')])
                message = {**message,'headers':headers}
            await send(message)

        try:
            await self.app(scope, receive, measured_send)
        except Exception:
            if started:
                # Streaming failures cannot start a second response.
                raise
            await JSONResponse({'detail':'Внутренняя ошибка сервиса. Повторите позже.','requestId':request_id},status_code=500)(scope,receive,measured_send)
        finally:
            route = getattr(scope.get('route'),'path','unmatched')
            method = scope.get('method','OTHER')
            if method not in ('GET','HEAD','POST','PUT','PATCH','DELETE','OPTIONS'):
                method = 'OTHER'
            self.logger.info(json.dumps(dict(event='http_request',requestId=request_id,method=method,route=route,status=status,durationMs=round((time.perf_counter()-start)*1000,2)),separators=(',',':')))
