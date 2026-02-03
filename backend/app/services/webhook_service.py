import hmac
import hashlib
from typing import Optional

from app.config import settings


class WebhookService:
    def __init__(self, secret: Optional[str] = None) -> None:
        self.secret = (secret or settings.GITHUB_WEBHOOK_SECRET or "").encode("utf-8")

    def verify_signature(
        self,
        body: bytes,
        signature_256: Optional[str] = None,
        signature_1: Optional[str] = None,
    ) -> bool:
        if not self.secret:
            return False

        if signature_256 and signature_256.startswith("sha256="):
            expected = self._sign(body, hashlib.sha256)
            # Constant-time compare to avoid timing attacks.
            return hmac.compare_digest(signature_256, expected)

        if signature_1 and signature_1.startswith("sha1="):
            expected = self._sign(body, hashlib.sha1)
            # Constant-time compare to avoid timing attacks.
            return hmac.compare_digest(signature_1, expected)

        return False

    def _sign(self, body: bytes, algo) -> str:
        digest = hmac.new(self.secret, body, algo).hexdigest()
        prefix = "sha256=" if algo is hashlib.sha256 else "sha1="
        return f"{prefix}{digest}"
