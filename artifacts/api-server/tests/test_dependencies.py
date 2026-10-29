"""Security regressions for the upgraded transitive Python dependencies."""

import base64
import unittest
from importlib.metadata import version

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519, ed448
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class DependencySecurityTests(unittest.TestCase):
    def test_security_version_floors(self):
        for package, floor in [("certifi", (2026, 10, 19)), ("pyjwt", (2, 15, 0))]:
            with self.subTest(package=package):
                self.assertGreaterEqual(tuple(map(int, version(package).split("."))), floor)

    def test_deep_unsigned_jwt_payload_is_a_decode_error(self):
        header = b64url(b'{"alg":"HS256","typ":"JWT"}')
        payload = b64url(b"[" * 20000 + b"]" * 20000)
        token = f"{header}.{payload}.{b64url(b'forged-signature')}"
        with self.assertRaises(jwt.DecodeError):
            jwt.decode(token, options={"verify_signature": False})

    def test_private_okp_jwk_must_match_its_public_key(self):
        for curve, key_type in [
            ("Ed25519", ed25519.Ed25519PrivateKey),
            ("Ed448", ed448.Ed448PrivateKey),
        ]:
            with self.subTest(curve=curve):
                holder = key_type.generate()
                attacker = key_type.generate()
                jwk = {
                    "kty": "OKP",
                    "crv": curve,
                    "alg": "EdDSA",
                    "x": b64url(holder.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)),
                    "d": b64url(holder.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())),
                }
                self.assertIsNotNone(jwt.PyJWK.from_dict(jwk).key)
                jwk["d"] = b64url(attacker.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
                with self.assertRaises(jwt.InvalidKeyError):
                    jwt.PyJWK.from_dict(jwk)
