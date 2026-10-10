"""Bounded asynchronous HTTP; never log URLs, tokens, bodies or exceptions."""

import asyncio
import json

import aiohttp

from ..errors import AuthenticationError, ProtocolError, ProtocolTimeout


def json_data(text):
    def constant(_):
        raise ValueError
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError
            result[k] = v
        return result
    try:
        return json.loads(text, parse_constant=constant, object_pairs_hook=pairs)
    except (ValueError, TypeError):
        raise ProtocolError("Invalid JSON protocol response") from None


class HTTP:
    def __init__(self, timeout, max_bytes, context=None, cookies=False, server_name=None, allow_put=False):
        self.timeout, self.max_bytes, self.context = timeout, max_bytes, context
        self.cookies = cookies
        self.server_name = server_name
        self.allow_put = allow_put
        self.session = None

    async def request(self, method, url, *, token=None, data=None, json=None):
        if method not in ("GET", "POST") and not (method == "PUT" and self.allow_put):
            raise ProtocolError("HTTP device write methods are disabled")
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout), trust_env=False,
                cookie_jar=aiohttp.CookieJar() if self.cookies else aiohttp.DummyCookieJar(),
                connector=aiohttp.TCPConnector(ssl=self.context if self.context is not None else True),
                headers={"Accept": "application/json", "Accept-Encoding": "identity"})
            if self.allow_put:
                # aiohttp 3.14.4 may retry PUT after a lost persistent connection.
                # Disable that pinned implementation feature for command sessions.
                if not hasattr(self.session, "_retry_connection"):
                    await self.close()
                    raise ProtocolError("HTTP command retry guard is unavailable")
                self.session._retry_connection = False
        headers = {"Authorization": "Bearer " + token} if token else {}
        try:
            async with self.session.request(method, url, data=data, json=json, headers=headers,
                                            allow_redirects=False, server_hostname=self.server_name) as response:
                parts, length = [], 0
                async for chunk in response.content.iter_chunked(16384):
                    length += len(chunk)
                    if length > self.max_bytes:
                        raise ProtocolError("HTTP response exceeds configured size limit")
                    parts.append(chunk)
                try:
                    text = b"".join(parts).decode("utf-8")
                except UnicodeError:
                    raise ProtocolError("HTTP response is not UTF-8") from None
                return response.status, dict(response.headers), text
        except asyncio.TimeoutError:
            raise ProtocolTimeout("HTTP request timed out") from None
        except (aiohttp.ClientError, OSError):
            raise ProtocolError("HTTP connection failed; check network/TLS and clock") from None

    async def get_json(self, method, url, **kwargs):
        status, _, body = await self.request(method, url, **kwargs)
        if status in (401, 403):
            raise AuthenticationError("HTTP authentication/permission denied")
        if not 200 <= status < 300:
            raise ProtocolError("HTTP read returned an unsuccessful status")
        return json_data(body)

    async def close(self):
        if self.session is not None:
            await self.session.close()
            self.session = None
