from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx
import jwt
from fastapi.security import HTTPBearer
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm

from app.core.config import settings


class InvalidTokenError(Exception):
    """Raised when a JWT token cannot be decoded or validated."""


class AzureConfigurationError(Exception):
    """Raised when Azure AD configuration is incomplete."""


bearer_scheme = HTTPBearer(auto_error=False)


class AzureADTokenVerifier:
    """Validate Azure Active Directory issued JWT bearer tokens."""

    def __init__(
        self,
        *,
        tenant_id: str | None,
        audience: str | None,
        authority_host: str,
        cache_seconds: int,
    ) -> None:
        self.tenant_id = tenant_id
        self.audience = audience
        self.authority_host = authority_host.rstrip("/")
        self.cache_seconds = cache_seconds
        self._openid_config: dict[str, Any] | None = None
        self._openid_expires_at = 0.0
        self._jwks: dict[str, Any] = {}
        self._jwks_expires_at = 0.0
        self._openid_lock = asyncio.Lock()
        self._jwks_lock = asyncio.Lock()

    @property
    def openid_configuration_url(self) -> str | None:
        if not self.tenant_id:
            return None
        return (
            f"{self.authority_host}/{self.tenant_id}/v2.0/.well-known/openid-configuration"
        )

    async def _fetch_json(self, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure defensive
            raise InvalidTokenError(f"Failed to fetch OpenID configuration from {url}") from exc
        return response.json()

    async def _get_openid_config(self) -> dict[str, Any]:
        if not self.openid_configuration_url:
            raise AzureConfigurationError("Azure tenant ID is not configured")

        async with self._openid_lock:
            now = time.time()
            if self._openid_config and now < self._openid_expires_at:
                return self._openid_config

            config = await self._fetch_json(self.openid_configuration_url)
            self._openid_config = config
            self._openid_expires_at = now + self.cache_seconds
            return config

    async def _get_jwks(self, *, force_refresh: bool = False) -> dict[str, Any]:
        async with self._jwks_lock:
            now = time.time()
            if self._jwks and not force_refresh and now < self._jwks_expires_at:
                return self._jwks

            config = await self._get_openid_config()
            jwks_uri = config.get("jwks_uri")
            if not jwks_uri:
                raise InvalidTokenError("Azure OpenID configuration is missing the jwks_uri")

            jwks_response = await self._fetch_json(jwks_uri)
            keys = jwks_response.get("keys", [])
            if not keys:
                raise InvalidTokenError("Azure JWKS endpoint did not return signing keys")

            self._jwks = {key["kid"]: key for key in keys if "kid" in key}
            self._jwks_expires_at = now + self.cache_seconds
            return self._jwks

    async def _get_signing_key(self, kid: str) -> dict[str, Any]:
        jwks = await self._get_jwks()
        key = jwks.get(kid)
        if key:
            return key
        jwks = await self._get_jwks(force_refresh=True)
        key = jwks.get(kid)
        if key:
            return key
        raise InvalidTokenError("Token key identifier not found in Azure JWKS")

    async def decode(self, token: str) -> dict[str, Any]:
        if not self.tenant_id or not self.audience:
            raise AzureConfigurationError(
                "Azure AD tenant ID and audience must be configured before decoding tokens"
            )

        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:
            raise InvalidTokenError("Unable to parse token header") from exc

        kid = header.get("kid")
        if not kid:
            raise InvalidTokenError("Token header is missing the key identifier (kid)")

        algorithm = header.get("alg")
        if algorithm != "RS256":
            raise InvalidTokenError("Unsupported signing algorithm for Azure AD token")

        key_dict = await self._get_signing_key(kid)
        try:
            public_key = RSAAlgorithm.from_jwk(json.dumps(key_dict))
        except Exception as exc:  # pragma: no cover - defensive against unexpected jwk format
            raise InvalidTokenError("Failed to construct public key from Azure JWKS") from exc

        config = await self._get_openid_config()
        issuer = config.get("issuer")
        if not issuer:
            raise InvalidTokenError("Azure OpenID configuration is missing the issuer")

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[algorithm],
                audience=self.audience,
                issuer=issuer,
                options={"require": ["aud", "iss", "exp"], "verify_aud": True},
            )
        except PyJWTError as exc:
            raise InvalidTokenError("Token signature or claims validation failed") from exc

        tenant = payload.get("tid") or payload.get("tenantId")
        if tenant and tenant != self.tenant_id:
            raise InvalidTokenError("Token tenant does not match expected tenant")

        audience_claim = payload.get("aud")
        if isinstance(audience_claim, str):
            audiences = {audience_claim}
        elif isinstance(audience_claim, (list, tuple, set)):
            audiences = set(audience_claim)
        else:
            audiences = set()

        if self.audience not in audiences:
            raise InvalidTokenError("Token audience does not include the configured audience")

        return payload


_azure_verifier = AzureADTokenVerifier(
    tenant_id=settings.azure_tenant_id,
    audience=settings.azure_expected_audience,
    authority_host=settings.azure_authority_host,
    cache_seconds=settings.azure_openid_cache_seconds,
)


async def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an Azure AD issued JWT access token."""

    try:
        return await _azure_verifier.decode(token)
    except AzureConfigurationError as exc:  # pragma: no cover - configuration guard
        raise InvalidTokenError(str(exc)) from exc

