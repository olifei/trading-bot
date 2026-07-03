"""PII / secret redaction helpers.

These are intentionally conservative: the trading domain is full of numbers
(prices, quantities), so we only redact patterns that are unambiguously
sensitive (emails, credentials, wallet-address / key-length hex strings and
phone numbers written with an explicit international prefix). Plain decimal
amounts are left untouched.
"""
import re
from typing import Any, Dict, Iterable

REDACTED = "[REDACTED]"

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# credentials written as `token: xxx`, `api_key=xxx`, `secret = xxx`, ...
_CREDENTIAL = re.compile(
    r"(?i)\b(bearer|token|api[_-]?key|secret|password|passwd|pwd)\b\s*[:=]\s*\S+"
)
# wallet addresses / private keys / access tokens: long hex or token-ish blobs
_LONG_HEX = re.compile(r"\b(?:0x)?[0-9a-fA-F]{32,}\b")
_GH_TOKEN = re.compile(r"\bgh[opsu]_[0-9A-Za-z]{20,}\b")
_GOOGLE_KEY = re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b")
# phone numbers requiring an explicit `+<countrycode>` so we don't eat prices
_PHONE = re.compile(r"\+\d[\d\s().\-]{7,}\d")

# Field names whose values should always be fully masked, regardless of content.
_SENSITIVE_KEYS = frozenset(
    {"password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
     "authorization", "access_token", "refresh_token", "private_key", "email"}
)


def redact(text: Any) -> Any:
    """Redact sensitive substrings from ``text``. Non-strings are returned as-is."""
    if not isinstance(text, str):
        return text
    text = _CREDENTIAL.sub(lambda m: f"{m.group(1)}: {REDACTED}", text)
    text = _GH_TOKEN.sub(REDACTED, text)
    text = _GOOGLE_KEY.sub(REDACTED, text)
    text = _EMAIL.sub(REDACTED, text)
    text = _LONG_HEX.sub(REDACTED, text)
    text = _PHONE.sub(REDACTED, text)
    return text


def redact_mapping(data: Any, _seen: Iterable[int] = ()) -> Any:
    """Recursively redact a dict/list structure for safe structured logging."""
    if isinstance(data, dict):
        out: Dict[Any, Any] = {}
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
                out[key] = REDACTED
            else:
                out[key] = redact_mapping(value)
        return out
    if isinstance(data, (list, tuple)):
        return [redact_mapping(v) for v in data]
    return redact(data)
