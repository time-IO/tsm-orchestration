from cachetools import TTLCache
from typing import Any
import json
import time
import requests
from jwcrypto import jwk, jwt
from jwcrypto.common import JWException
from config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger("app.auth")


class OIDCError(Exception):
    pass


class OIDCService:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        cache_ttl: int = 600,
        clock_skew: int = 30,
        request_timeout: float = 5.0,
    ):
        self.issuer = issuer
        self.audience = audience

        self.request_timeout = request_timeout
        self.clock_skew = clock_skew

        self._config_cache = TTLCache(maxsize=1, ttl=cache_ttl)
        self._jwks_cache = TTLCache(maxsize=1, ttl=cache_ttl)

    def _get_oidc_config(self) -> dict[str, Any]:
        logger.debug(f"Fetching OIDC configuration from {settings.OIDC_WELL_KNOWN}")
        try:
            return self._config_cache["config"]
        except KeyError:
            url = settings.OIDC_WELL_KNOWN

            resp = requests.get(url, timeout=self.request_timeout)
            resp.raise_for_status()

            config = resp.json()

            if config.get("issuer") != self.issuer:
                raise OIDCError("OIDC issuer mismatch")

            self._config_cache["oidc_config"] = config
            return config

    def _get_jwks(self) -> jwk.JWKSet:
        try:
            return self._jwks_cache["jwks"]
        except KeyError:
            config = self._get_oidc_config()
            jwks_uri = config["jwks_uri"]

            logger.debug(f"Fetching JWKS from {jwks_uri}")

            resp = requests.get(jwks_uri, timeout=self.request_timeout)
            resp.raise_for_status()

            jwks = jwk.JWKSet.from_json(resp.text)
            self._jwks_cache["jwks"] = jwks
            return jwks

    def verify_access_token(self, token: str) -> dict[str, Any]:
        try:
            return self._verify(token)
        except JWException:
            # likely key rotation → retry once
            self._jwks_cache.pop("jwks", None)
            return self._verify(token)

    def _verify(self, token: str) -> dict[str, Any]:
        jwks = self._get_jwks()

        try:
            jwt_token = jwt.JWT(
                jwt=token,
                key=jwks,
                expected_type="JWS",
            )

            claims = json.loads(jwt_token.claims)
        except:
            logger.exception("Failed to verify JWT")
            raise HTTPException(status_code=401, detail="Invalid Token")
        self._validate_claims(claims)
        return claims

    def _validate_claims(self, claims: dict[str, Any]) -> None:
        if claims.get("iss") != self.issuer:
            logger.error(f"Invalid issuer: {claims.get('iss')}")
            raise OIDCError("Invalid issuer")

        aud = claims.get("aud")
        aud = [aud] if isinstance(aud, str) else aud or []
        if self.audience not in aud:
            logger.error(f"Invalid audience: {aud}")
            raise OIDCError("Invalid audience")

        now = int(time.time())
        exp = claims.get("exp")
        if exp is None or exp < now - self.clock_skew:
            logger.error(f"Token expired")
            raise OIDCError("Token expired")

    def fetch_userinfo(self, access_token: str) -> dict[str, Any]:
        config = self._get_oidc_config()
        userinfo_endpoint = config.get("userinfo_endpoint")

        if not userinfo_endpoint:
            raise OIDCError("Userinfo endpoint not available")

        logger.debug(f"Fetching userinfo from {userinfo_endpoint}")
        resp = requests.get(
            userinfo_endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            timeout=self.request_timeout,
        )

        if resp.status_code != 200:
            logger.error(f"Failed to fetch userinfo: {resp.status_code} {resp.text}")
            raise OIDCError("Failed to fetch userinfo")

        return resp.json()

    def authenticate(self, *, access_token: str) -> dict[str, Any]:
        claims = self.verify_access_token(access_token)

        if "sub" not in claims:
            raise OIDCError("Missing subject claim")

        return claims


oidc = OIDCService(
    issuer=settings.OIDC_ISSUER,
    audience=settings.OIDC_AUDIENCE,
)
