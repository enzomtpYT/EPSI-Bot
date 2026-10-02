"""Security utilities for URL validation, SSRF protection, and input sanitization."""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlsplit

from aiohttp.abc import ResolveResult
from aiohttp.resolver import ThreadedResolver

logger = logging.getLogger(__name__)

# Maximum permissible iCal download size (5 MB)
MAX_ICAL_DOWNLOAD_BYTES = 5 * 1024 * 1024


def is_ip_forbidden(ip_str: str) -> bool:
    """Return True if IP is private, loopback, link-local, reserved, multicast, or unspecified."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return bool(
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_safe_url(url: str | None) -> str:
    """Validate and sanitize external URL to prevent SSRF and unsafe protocols.

    - Rejects non-HTTP(S) schemes (normalizes webcal:// to https://).
    - Resolves hostnames via DNS and verifies that all resolved IP addresses are public.
    - Rejects localhost, loopback, private ranges, link-local (cloud metadata), and reserved IPs.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL invalide ou vide.")

    clean_url = url.strip()

    # Normalize webcal:// to https://
    if clean_url.startswith("webcal://"):
        clean_url = "https://" + clean_url[len("webcal://") :]

    parsed = urlsplit(clean_url)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(
            "Protocole non autorisé : seuls les protocoles HTTP et HTTPS sont acceptés."
        )

    # Restrict allowed ports to standard web ports (80, 443)
    port = parsed.port
    if port is not None and port not in {80, 443}:
        raise ValueError(f"Port non autorisé ({port}) : seuls les ports 80 et 443 sont acceptés.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Hôte URL manquant ou invalide.")

    # Check for direct localhost naming
    if hostname.lower() in {"localhost", "localhost.localdomain"} or hostname.lower().endswith(
        ".localhost"
    ):
        raise ValueError("Accès aux hôtes locaux non autorisé (SSRF protection).")

    # If hostname is an IP literal
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if is_ip_forbidden(str(ip_obj)):
            raise ValueError("Accès aux adresses IP privées ou locales non autorisé.")
        return clean_url
    except ValueError as e:
        if "Accès" in str(e):
            raise
        # Hostname is a domain name, not an IP literal. Continue to DNS check.
        pass

    # Resolve hostname via DNS and check all resolved IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        if not addr_info:
            raise ValueError(f"Impossible de résoudre le nom d'hôte : {hostname}")

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = str(sockaddr[0])
            if is_ip_forbidden(ip_str):
                raise ValueError(
                    f"Le nom d'hôte {hostname} résout vers une adresse IP interne ou interdite ({ip_str})."
                )
    except socket.gaierror as e:
        raise ValueError(f"Erreur de résolution DNS pour {hostname} : {e}")

    return clean_url


def is_safe_http_url(url: str | None) -> bool:
    """Check if an external URL (such as a Teams link) is a safe HTTPS/HTTP link."""
    if not url or not isinstance(url, str):
        return False
    clean = url.strip()
    if not (clean.startswith("https://") or clean.startswith("http://")):
        return False
    # Avoid JavaScript/data/vbscript scheme evasion
    lower = clean.lower()
    if any(lower.startswith(bad) for bad in ("javascript:", "data:", "vbscript:", "file:")):
        return False
    return True


class SafeResolver(ThreadedResolver):
    """DNS resolver that validates resolved IP addresses to defeat DNS rebinding attacks."""

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        records = await super().resolve(host, port, family)
        for r in records:
            ip_str = str(r.get("host", ""))
            if is_ip_forbidden(ip_str):
                raise ValueError(
                    f"Tentative de DNS rebinding bloquée : {host} résout vers une IP locale ou privée ({ip_str})."
                )
        return records
