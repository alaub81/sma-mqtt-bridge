"""Normal-account ennexOS PKCE session, separate from local API."""

import asyncio
import base64
import hashlib
import secrets
import time
from html.parser import HTMLParser
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit

from ..errors import AuthenticationError, ProtocolError
from ..model import Property, number
from .http import HTTP, json_data


def transient_login_status(status):
    if status in (408, 429) or 500 <= status <= 599:
        raise ProtocolError("Portal login service temporarily unavailable")


class LoginParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.actions = []
        self.forms = []
        self.current_form = None
        self.challenge = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current_form = {
                "action": attrs.get("action", ""),
                "inputs": set(),
                "method": attrs.get("method", "").lower(),
            }
            self.forms.append(self.current_form)
            if attrs.get("id") == "kc-form-login":
                self.actions.append(attrs.get("action", ""))
        if tag == "input" and self.current_form is not None:
            self.current_form["inputs"].add((attrs.get("name"), attrs.get("type", "text").lower()))
        if (
            tag == "input"
            and attrs.get("type") != "hidden"
            and attrs.get("name", "").lower()
            in {
                "otp",
                "totp",
                "otpcode",
                "captcha",
                "captcha_response",
                "password-new",
                "password-confirm",
            }
        ):
            self.challenge = True

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None


def login_action(text, auth_base):
    parser = LoginParser()
    parser.feed(text)
    # The current SMA login page has one credential form without an ID.
    if not parser.actions and len(parser.forms) == 1:
        form = parser.forms[0]
        if (
            form["method"] == "post"
            and {("username", "text"), ("password", "password")} <= form["inputs"]
        ):
            parser.actions.append(form["action"])
    if parser.challenge or len(parser.actions) != 1:
        raise AuthenticationError("Portal login needs an interactive step or its form changed")
    target = urljoin(auth_base + "/", parser.actions[0])
    expected, actual = urlsplit(auth_base), urlsplit(target)
    if (
        actual.scheme != "https"
        or actual.netloc != expected.netloc
        or actual.username
        or actual.fragment
        or not actual.path.startswith(expected.path.rstrip("/") + "/login-actions/")
    ):
        raise AuthenticationError("Portal login form action is not a trusted endpoint")
    return target


def authorization_code(location, redirect, state):
    actual, expected = urlsplit(location), urlsplit(redirect)
    items = parse_qsl(actual.query, keep_blank_values=True)
    values = dict(items)
    if (
        actual.scheme != "https"
        or actual.netloc != expected.netloc
        or actual.path != expected.path
        or actual.fragment
        or actual.username
        or len(items) != len(values)
        or values.get("state") != state
        or not values.get("code")
    ):
        raise AuthenticationError("Portal redirect/state is invalid")
    return values["code"]


def portal_values(reply, plant_id, device_id):
    if (
        not isinstance(reply, dict)
        or str(reply.get("plantId")) != plant_id
        or str(reply.get("deviceId")) != device_id
        or reply.get("productTagId") != 19143
        or not isinstance(reply.get("consumerTypes"), list)
        or "EVehicle" not in reply["consumerTypes"]
    ):
        raise ProtocolError("Portal reply does not identify the configured eCharger")
    demand = reply.get("optionalEnergyDemand")
    if not isinstance(demand, dict):
        raise ProtocolError("Missing portal charging preference")
    pv = demand.get("minPvPercentage")
    if (
        demand.get("isOptionalConsumer") is not True
        or type(pv) is not int
        or not 0 <= pv <= 100
        or (demand.get("pvSurplusOnly") is not None and type(demand["pvSurplusOnly"]) is not bool)
        or type(demand.get("usePriceLimit")) is not bool
        or (
            demand.get("priceLimit") is not None
            and (
                type(demand["priceLimit"]) not in (int, float)
                or number(demand["priceLimit"]) is None
            )
        )
    ):
        raise ProtocolError("Invalid portal charging preference fields")
    links = reply.get("_links", {})
    writable = isinstance(links, dict) and isinstance(
        links.get("ui_Edit_OptionalEnergyDemand"), list
    )
    mode = (
        "Kostenlimit; PV-Prozentwert derzeit inaktiv"
        if demand["usePriceLimit"]
        else "PV-Anteil mit besonderer Überschussoption"
        if demand.get("pvSurplusOnly") is True
        else "Mindest-PV-Anteil"
    )
    return {
        "portal/pv-minimum": pv,
        "portal/grid-share": 100 - pv,
        "portal/writable": writable,
        "portal/setting-mode": mode,
    }


class PortalReader:
    properties = (
        Property(
            "portal", "pv-minimum", "Minimum PV preference", "integer", "%", required_for_ready=True
        ),
        Property("portal", "grid-share", "Allowed grid preference", "integer", "%"),
        Property("portal", "writable", "Portal edit permission", "boolean"),
        Property("portal", "setting-mode", "Preference mode", "string"),
    )

    def __init__(self, settings, max_bytes):
        self.settings = settings
        self.http = HTTP(settings.timeout_seconds, max_bytes, cookies=True)
        self.token, self.refresh, self.expires = None, None, 0
        self.lock = asyncio.Lock()
        self.redirect = settings.base_url.rstrip("/") + "/dashboard/initialize"
        self.token_url = settings.auth_base_url.rstrip("/") + "/protocol/openid-connect/token"

    def store_tokens(self, text):
        reply = json_data(text)
        if not isinstance(reply, dict):
            raise AuthenticationError("Invalid portal token response")
        token, lifetime = reply.get("access_token"), number(reply.get("expires_in"))
        if (
            not isinstance(token, str)
            or not token
            or any(c.isspace() for c in token)
            or lifetime is None
            or lifetime <= 0
        ):
            raise AuthenticationError("Portal login did not return a valid token/lifetime")
        self.token = token
        refresh = reply.get("refresh_token")
        self.refresh = (
            refresh
            if isinstance(refresh, str) and refresh and not any(c.isspace() for c in refresh)
            else None
        )
        self.expires = time.monotonic() + max(0, float(lifetime) - 30)
        return token

    async def access_token(self):
        if self.token and time.monotonic() < self.expires:
            return self.token
        if self.refresh:
            status, _, body = await self.http.request(
                "POST",
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh,
                    "client_id": self.settings.client_id,
                },
            )
            if status == 200:
                return self.store_tokens(body)
            self.token, self.refresh = None, None
            if status not in (400, 401):
                raise ProtocolError("Portal token renewal failed")
        verifier, state = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        auth_url = (
            self.settings.auth_base_url.rstrip("/")
            + "/protocol/openid-connect/auth?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": self.settings.client_id,
                    "redirect_uri": self.redirect,
                    "scope": "openid profile",
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                }
            )
        )
        status, _, body = await self.http.request("GET", auth_url)
        transient_login_status(status)
        if status != 200:
            raise AuthenticationError("Portal login page is unavailable or requires interaction")
        action = login_action(body, self.settings.auth_base_url)
        status, headers, _ = await self.http.request(
            "POST",
            action,
            data={
                "username": self.settings.username.strip(),
                "password": self.settings.password,
                "credentialId": "",
            },
        )
        transient_login_status(status)
        if status not in (302, 303):
            raise AuthenticationError(
                "Portal login rejected or requires MFA/CAPTCHA/password interaction"
            )
        code = authorization_code(headers.get("Location", ""), self.redirect, state)
        status, _, body = await self.http.request(
            "POST",
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect,
                "code_verifier": verifier,
                "client_id": self.settings.client_id,
            },
        )
        transient_login_status(status)
        if status != 200:
            raise AuthenticationError("Portal authorization code exchange failed")
        return self.store_tokens(body)

    def device_url(self):
        s = self.settings
        return (
            s.api_base_url.rstrip("/")
            + "/plants/"
            + quote(s.plant_id, safe="")
            + "/devices/"
            + quote(s.device_id, safe="")
        )

    async def read_device(self):
        s = self.settings
        url = self.device_url() + "?menuItemType=ViewDeviceProperties"
        for attempt in range(2):
            status, _, body = await self.http.request("GET", url, token=await self.access_token())
            if status == 401 and attempt == 0:
                self.token, self.expires = None, 0
                continue
            if status in (401, 403):
                raise AuthenticationError("Portal device access denied")
            if status != 200:
                raise ProtocolError("Portal device read failed")
            reply = json_data(body)
            portal_values(reply, s.plant_id, s.device_id)
            return reply

    async def read(self):
        async with self.lock:
            s = self.settings
            return portal_values(await self.read_device(), s.plant_id, s.device_id)

    async def close(self):
        self.token, self.refresh = None, None
        await self.http.close()
