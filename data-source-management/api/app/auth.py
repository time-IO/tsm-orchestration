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

        logger.debug(
            "OIDC service initialized (issuer=%s audience=%s cache_ttl=%s timeout=%s)",
            self.issuer,
            self.audience,
            cache_ttl,
            self.request_timeout,
        )

    def _get_oidc_config(self) -> dict[str, Any]:
        logger.debug("Loading OIDC configuration")
        try:
            logger.debug("OIDC configuration cache HIT")
            return self._config_cache["config"]
        except KeyError:
            url = settings.OIDC_WELL_KNOWN
            logger.debug(f"OIDC configuration cache MISS, fetching from {url}")

            try:
                resp = requests.get(url, timeout=self.request_timeout)
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.error("Failed to fetch OIDC configuration from %s: %s", url, exc)
                raise OIDCError("Failed to fetch OIDC configuration") from exc

            config = resp.json()

            if config.get("issuer") != self.issuer:
                logger.error(
                    "OIDC issuer mismatch from discovery: expected=%s got=%s",
                    self.issuer,
                    config.get("issuer"),
                )
                raise OIDCError("OIDC issuer mismatch")

            self._config_cache["config"] = config
            logger.debug("OIDC configuration cached successfully")
            return config

    def _get_jwks(self) -> jwk.JWKSet:
        try:
            logger.debug("JWKS cache HIT")
            return self._jwks_cache["jwks"]
        except KeyError:
            config = self._get_oidc_config()
            jwks_uri = config["jwks_uri"]

            logger.debug(f"JWKS cache MISS, fetching from {jwks_uri}")

            try:
                resp = requests.get(jwks_uri, timeout=self.request_timeout)
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.error("Failed to fetch JWKS from %s: %s", jwks_uri, exc)
                raise OIDCError("Failed to fetch JWKS") from exc

            jwks = jwk.JWKSet.from_json(resp.text)
            self._jwks_cache["jwks"] = jwks
            logger.debug("JWKS cached successfully")
            return jwks

    def verify_access_token(self, token: str) -> dict[str, Any]:
        try:
            return self._verify(token)
        except JWException:
            # likely key rotation → retry once
            logger.warning("JWT verification failed; refreshing JWKS and retrying once")
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
        try:
            resp = requests.get(
                userinfo_endpoint,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=self.request_timeout,
            )
        except requests.RequestException as exc:
            logger.exception("Failed to call userinfo endpoint")
            raise OIDCError("Failed to fetch userinfo") from exc

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
