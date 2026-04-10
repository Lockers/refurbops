from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

import jwt

from app.config import get_settings


class TokenService:
    def _normalize_pem(self, value: str) -> str:
        return value.replace("\\n", "\n").strip()

    def _read_key_file(self, relative_path: str) -> str:
        backend_root = Path(__file__).resolve().parents[2]
        key_path = backend_root / relative_path
        return key_path.read_text(encoding="utf-8").strip()

    def _get_private_key(self) -> str:
        settings = get_settings()
        if settings.jwt_private_key_pem:
            return self._normalize_pem(settings.jwt_private_key_pem)
        if settings.jwt_private_key_path:
            return self._read_key_file(settings.jwt_private_key_path)
        raise RuntimeError("JWT private key is not configured")

    def _get_public_key(self) -> str:
        settings = get_settings()
        if settings.jwt_public_key_pem:
            return self._normalize_pem(settings.jwt_public_key_pem)
        if settings.jwt_public_key_path:
            return self._read_key_file(settings.jwt_public_key_path)
        raise RuntimeError("JWT public key is not configured")

    def issue_access_token(
        self,
        *,
        user: dict[str, Any],
        session_public_id: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        settings = get_settings()
        payload = {
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "sub": user["public_id"],
            "sid": session_public_id,
            "typ": "access",
            "email": user["email"],
            "principal_type": user["principal_type"],
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(
            payload,
            self._get_private_key(),
            algorithm="EdDSA",
            headers={"kid": settings.jwt_active_kid},
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        settings = get_settings()
        return jwt.decode(
            token,
            self._get_public_key(),
            algorithms=["EdDSA"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )

    def generate_opaque_token_value(self, *, public_id: str) -> tuple[str, str]:
        secret = secrets.token_urlsafe(48)
        token_value = f"{public_id}.{secret}"
        token_hash = self.hash_refresh_token_value(token_value)
        return token_value, token_hash

    def generate_refresh_token_value(self, *, public_id: str) -> tuple[str, str]:
        return self.generate_opaque_token_value(public_id=public_id)

    @staticmethod
    def hash_refresh_token_value(token_value: str) -> str:
        return hashlib.sha256(token_value.encode("utf-8")).hexdigest()

    @staticmethod
    def extract_refresh_public_id(token_value: str) -> str:
        public_id, _, _ = token_value.partition(".")
        return public_id.strip()

    @staticmethod
    def extract_opaque_public_id(token_value: str) -> str:
        public_id, _, _ = token_value.partition(".")
        return public_id.strip()


token_service = TokenService()
