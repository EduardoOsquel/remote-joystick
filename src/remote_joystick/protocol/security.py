from __future__ import annotations

import hmac
import hashlib


class HMACSigner:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def sign(self, payload: bytes) -> bytes:
        return hmac.new(self.key, payload, hashlib.sha256).digest()

    def verify(self, payload: bytes, signature: bytes) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
