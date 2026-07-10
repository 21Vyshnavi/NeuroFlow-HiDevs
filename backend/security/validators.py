# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import ipaddress
import re
import urllib.parse

import bleach
from fastapi import HTTPException, status

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)

def validate_query_text(text: str) -> str:
    sanitized = sanitize_text(text)
    if len(sanitized) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text exceeds maximum length of 5000 characters."
        )
    return sanitized

def validate_pipeline_name(name: str) -> str:
    sanitized = sanitize_text(name)
    if len(sanitized) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline name exceeds maximum length of 100 characters."
        )
    return sanitized

def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False

def validate_url(url: str) -> str:
    if not url:
        return url
    if not URL_PATTERN.match(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must match http:// or https://"
        )
    
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL hostname."
        )
    
    if is_private_ip(hostname) or hostname.lower() == "localhost":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSRF Protection: Access to private IP ranges or localhost is blocked."
        )
    
    import socket
    try:
        ips = socket.getaddrinfo(hostname, None)
        for ip in ips:
            ip_addr = ip[4][0]
            if is_private_ip(ip_addr):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SSRF Protection: Hostname resolves to private IP address range."
                )
    except socket.gaierror:
        pass
        
    return url

def validate_file_type(file_bytes: bytes, filename: str, expected_type: str = None) -> None:
    if not file_bytes:
        return
        
    ext = filename.split(".")[-1].lower()
    
    # Direct magic bytes checks
    # Executable headers
    if file_bytes.startswith(b"MZ") or file_bytes.startswith(b"\x7fELF") or file_bytes.startswith(b"\xca\xfe\xba\xbe") or file_bytes.startswith(b"\xce\xfa\xed\xfe") or file_bytes.startswith(b"\xcf\xfa\xed\xfe"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malicious file validation: Executable files are not allowed."
        )
        
    # PDF: should start with %PDF
    if ext == "pdf" and not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MIME type mismatch: .pdf file does not start with PDF magic bytes."
        )
        
    # Images: PNG, JPEG
    if ext == "png" and not file_bytes.startswith(b"\x89PNG"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MIME type mismatch: .png file does not start with PNG magic bytes."
        )
        
    if ext in ["jpg", "jpeg"] and not file_bytes.startswith(b"\xff\xd8\xff"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MIME type mismatch: image file does not start with JPEG magic bytes."
        )
        
    # CSV/TXT: should not contain null bytes indicating raw binary formats
    if ext in ["csv", "txt"] and b"\x00" in file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MIME type mismatch: Text file contains binary null bytes."
        )
