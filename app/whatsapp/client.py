"""Python HTTP client for the Baileys WhatsApp gateway (Node sidecar).

Chama o gateway em ``settings.baileys_gateway_url`` (default http://localhost:3001):

- GET  /qr          -> {qr, status}
- POST /send        -> envia texto            {to, message}
- POST /send-media  -> envia ficheiro (JSON base64) {to, fileBase64, filename, mimetype, caption}

So depende de httpx + app.config.
"""
from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppGatewayError(Exception):
    pass


def _normalize_jid(to: str) -> str:
    """Normalize a phone number to a WhatsApp JID (digits@s.whatsapp.com).

    Already-formatted JIDs (containing '@') are returned unchanged.
    """
    raw = to or ""
    if "@" in raw:
        return raw
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return raw
    return f"{digits}@s.whatsapp.com"


class WhatsAppGatewayClient:
    """Async client for the Baileys REST gateway."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = (base_url or settings.baileys_gateway_url).rstrip("/")
        self.timeout = timeout

    async def get_qr(self) -> dict:
        """Returns {'qr': str|None, 'status': 'waiting'|'connected'|'unavailable'|...}."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/qr")
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.warning("WhatsApp gateway /qr error: %s", e)
            return {"qr": None, "status": "unavailable", "error": str(e)}

    async def send_text(self, to: str, message: str) -> dict:
        """Send a text message. Raises WhatsAppGatewayError on failure."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/send",
                    json={"to": _normalize_jid(to), "message": message},
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("WhatsApp gateway /send error: %s", e)
            raise WhatsAppGatewayError(str(e))

    async def send_media(self, to: str, file_path: str, caption: str = "") -> dict:
        """Send a file (image/document) as base64 JSON to /send-media."""
        path = Path(file_path)
        if not path.exists():
            raise WhatsAppGatewayError(f"file not found: {file_path}")
        content = path.read_bytes()
        mimetype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(content).decode("ascii")
        payload: dict = {
            "to": _normalize_jid(to),
            "fileBase64": encoded,
            "filename": path.name,
            "mimetype": mimetype,
        }
        if caption:
            payload["caption"] = caption
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/send-media", json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("WhatsApp gateway /send-media error: %s", e)
            raise WhatsAppGatewayError(str(e))


whatsapp_client = WhatsAppGatewayClient()
