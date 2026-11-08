import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import Settings
from app.security.clerk import ClerkTokenVerifier


class SigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class StaticJWKClient:
    def __init__(self, key: object) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, _: str) -> SigningKey:
        return SigningKey(self._key)


def verifier(public_key: object) -> ClerkTokenVerifier:
    instance = object.__new__(ClerkTokenVerifier)
    instance._settings = Settings(  # noqa: SLF001
        clerk_issuer="https://issuer.example",
        clerk_authorized_parties="gonarra://",
    )
    instance._client = StaticJWKClient(public_key)  # type: ignore[assignment]  # noqa: SLF001
    return instance


def token(private_key: object, *, authorized_party: str | None = "gonarra://") -> str:
    now = int(time.time())
    claims: dict[str, object] = {
        "iss": "https://issuer.example",
        "sub": "user_123",
        "sid": "session_123",
        "iat": now,
        "nbf": now,
        "exp": now + 60,
    }
    if authorized_party is not None:
        claims["azp"] = authorized_party
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
    )


def test_verifier_accepts_expected_issuer_and_party() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    user = verifier(private_key.public_key()).verify(token(private_key))
    assert user.subject == "user_123"
    assert user.session_id == "session_123"


def test_verifier_rejects_unapproved_party() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(jwt.InvalidTokenError):
        verifier(private_key.public_key()).verify(
            token(private_key, authorized_party="https://untrusted.example")
        )


def test_verifier_accepts_token_without_party_claim() -> None:
    # Native Clerk session tokens (Expo / React Native) carry no ``azp``.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    user = verifier(private_key.public_key()).verify(token(private_key, authorized_party=None))
    assert user.subject == "user_123"
    assert user.session_id == "session_123"


def test_verifier_rejects_wrong_party_even_with_native_tokens_allowed() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(jwt.InvalidTokenError, match="Unauthorized token party"):
        verifier(private_key.public_key()).verify(
            token(private_key, authorized_party="https://evil.example")
        )
