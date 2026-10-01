"""Unit tests for cybersecurity protections (SSRF, XSS helpers, OAuth CSRF, headers, DoS limits)."""

import pytest
from httpx import ASGITransport, AsyncClient

from services.embed_builder import safe_truncate
from services.security import (
    is_ip_forbidden,
    is_safe_http_url,
    validate_safe_url,
)
from web.app import create_web_app


def test_is_ip_forbidden():
    """Verify private, loopback, link-local, and reserved IPs are flagged."""
    # Loopback
    assert is_ip_forbidden("127.0.0.1") is True
    assert is_ip_forbidden("127.0.0.5") is True
    assert is_ip_forbidden("::1") is True

    # Cloud metadata / Link-local
    assert is_ip_forbidden("169.254.169.254") is True
    assert is_ip_forbidden("fe80::1") is True

    # Private ranges
    assert is_ip_forbidden("10.0.0.1") is True
    assert is_ip_forbidden("172.16.0.1") is True
    assert is_ip_forbidden("192.168.1.1") is True

    # Public IPs
    assert is_ip_forbidden("8.8.8.8") is False
    assert is_ip_forbidden("1.1.1.1") is False

    # Non-IP string
    assert is_ip_forbidden("not-an-ip") is False


def test_validate_safe_url():
    """Verify SSRF filters reject internal and unsafe URLs."""
    # Empty / non-string
    with pytest.raises(ValueError, match="URL invalide"):
        validate_safe_url("")

    # Dangerous schemes
    with pytest.raises(ValueError, match="Protocole non autorisé"):
        validate_safe_url("file:///etc/passwd")

    with pytest.raises(ValueError, match="Protocole non autorisé"):
        validate_safe_url("ftp://example.com/test.ics")

    # Localhost / Loopback
    with pytest.raises(
        ValueError, match="Accès aux hôtes locaux non autorisé|Accès aux adresses IP"
    ):
        validate_safe_url("http://localhost:8080/secret")

    with pytest.raises(ValueError, match="Accès aux adresses IP privées"):
        validate_safe_url("http://127.0.0.1:8080/test")

    # Cloud metadata
    with pytest.raises(ValueError, match="Accès aux adresses IP privées"):
        validate_safe_url("http://169.254.169.254/latest/meta-data/")

    # Private IP
    with pytest.raises(ValueError, match="Accès aux adresses IP privées"):
        validate_safe_url("http://192.168.1.254/admin")

    # Webcal normalization
    normalized = validate_safe_url("webcal://1.1.1.1/cal.ics")
    assert normalized == "https://1.1.1.1/cal.ics"


def test_is_safe_http_url():
    """Verify safe HTTP link checker blocks javascript and bad schemes."""
    assert is_safe_http_url("https://teams.microsoft.com/l/meetup-join/123") is True
    assert is_safe_http_url("http://example.com") is True
    assert is_safe_http_url("javascript:alert(1)") is False
    assert is_safe_http_url("data:text/html,<script>alert(1)</script>") is False
    assert is_safe_http_url("vbscript:msgbox") is False
    assert is_safe_http_url("") is False
    assert is_safe_http_url(None) is False


def test_safe_truncate():
    """Verify Discord Embed limit truncation."""
    short = "Hello World"
    assert safe_truncate(short, 20) == short

    exact = "A" * 20
    assert safe_truncate(exact, 20) == exact

    overflow = "A" * 25
    truncated = safe_truncate(overflow, 20)
    assert len(truncated) == 20
    assert truncated.endswith("...")


@pytest.mark.asyncio
async def test_security_headers_middleware():
    """Verify security headers are applied to HTTP responses."""
    app = create_web_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/manifest.json")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "SAMEORIGIN"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in resp.headers


@pytest.mark.asyncio
async def test_oauth_csrf_state_protection():
    """Verify OAuth2 callback rejects requests without a valid matching state."""
    app = create_web_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request callback with forged code and without session state
        resp = await client.get(
            "/auth/callback?code=fake_code&state=fake_state", follow_redirects=False
        )
        assert resp.status_code == 307
        assert "error=csrf_state_invalid" in resp.headers.get("location", "")
