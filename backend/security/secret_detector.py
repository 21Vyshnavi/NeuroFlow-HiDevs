import re
import logging

logger = logging.getLogger(__name__)

SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "generic_api_key": re.compile(r"['\"]?(?:api|secret|token|key|password)['\"]?\s*[:=]\s*['\"]([A-Za-z0-9/+]{20,})['\"]", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "jwt_token": re.compile(r"[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+")
}

def scan_and_redact_secrets(text: str, document_id: str = "unknown") -> tuple[str, list[dict]]:
    if not text:
        return text, []
    
    redacted_text = text
    redactions = []
    
    for pattern_name, pattern in SECRET_PATTERNS.items():
        matches = list(pattern.finditer(redacted_text))
        if matches:
            # We sort matches in reverse order to redact from back to front without messing up indices
            for match in sorted(matches, key=lambda m: m.start(), reverse=True):
                val = match.group(0)
                # For generic api key, we might want to only redact the captured group or the entire match.
                # Redacting the entire match or just the key value: let's redact the sensitive part or the whole match.
                # Redacting the whole match with '[REDACTED]' is safer and simpler.
                start, end = match.span()
                redacted_text = redacted_text[:start] + "[REDACTED]" + redacted_text[end:]
                
                log_payload = {
                    "event": "secret_redacted",
                    "document_id": document_id,
                    "pattern_type": pattern_name
                }
                logger.warning(f"Secret detected and redacted: {log_payload}")
                redactions.append(log_payload)
                
    return redacted_text, redactions
