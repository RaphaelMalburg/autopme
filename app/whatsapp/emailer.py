"""Resend emailer (httpx) for the WhatsApp module.

Portado de agente-consultoria/app/services/resend_emailer.py. Usa httpx diretamente
(NAO o SDK resend) para zero dependencias extra alem de httpx + app.config.

A funcao ``build_extraction_email_html`` e PURA (sem rede) para que o router possa
devolver um ``email_preview`` sem enviar, e para ser testada offline.
"""
from __future__ import annotations

import asyncio
import html as _html
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class ResendEmailerError(Exception):
    pass


def _esc(value) -> str:
    """HTML-escape an arbitrary value for safe email rendering."""
    return _html.escape("" if value is None else str(value))


def _render_value(value) -> str:
    """Render a scalar/list/dict value as safe HTML text."""
    if isinstance(value, (list, dict)):
        return _esc(json.dumps(value, ensure_ascii=False))
    return _esc(value)


def build_extraction_email_html(
    business_name: str,
    extracted_data: Optional[dict],
    status: str = "extracted",
    low_confidence_fields: Optional[dict] = None,
    source_label: str = "",
) -> str:
    """Pure function: build the HTML body for a document-extraction email.

    No network. Safe for unit testing and for returning as ``email_preview``.
    """
    name = _esc(business_name or "Negocio")
    rows = []
    if isinstance(extracted_data, dict):
        for key, value in extracted_data.items():
            if key == "confianca":
                continue
            rows.append(f"<li><strong>{_esc(key)}</strong>: {_render_value(value)}</li>")
    fields_html = f"<ul>{''.join(rows)}</ul>" if rows else "<p>(sem dados extraidos)</p>"

    warnings_html = ""
    if low_confidence_fields:
        items = "".join(
            f"<li>{_esc(k)}: confianca {_esc(v)}</li>"
            for k, v in low_confidence_fields.items()
        )
        warnings_html = f"<h3>Campos com baixa confianca</h3><ul>{items}</ul>"

    source_html = f"<p>Origem: {_esc(source_label)}</p>" if source_label else ""

    return (
        f"<h2>Extracao de Documento - {name}</h2>\n"
        f"<p>Estado: <strong>{_esc(status)}</strong></p>\n"
        f"{source_html}\n"
        f"<h3>Dados Extraidos</h3>\n"
        f"{fields_html}\n"
        f"{warnings_html}"
    ).strip()


class ResendEmailer:
    """Async Resend client via httpx with retry."""

    def __init__(self):
        self.api_key = settings.resend_api_key
        self.email_from = settings.email_from
        self.notify_email = settings.demo_notify_email

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str = "",
    ) -> dict:
        """Send an email via Resend. Returns {status, resend_message_id?, sent_at?, error_message?}."""
        payload: dict = {
            "from": self.email_from,
            "to": [to],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            payload["text"] = text_body

        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        RESEND_API_URL,
                        headers=self._headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    logger.info("Email sent to %s: %s", to, subject)
                    return {
                        "status": "sent",
                        "resend_message_id": data.get("id"),
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                    }
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("Resend HTTP %d (attempt %d/3)", e.response.status_code, attempt + 1)
                if e.response.status_code in (400, 401, 403):
                    break
            except Exception as e:
                last_error = e
                logger.warning("Resend error (attempt %d/3): %s", attempt + 1, type(e).__name__)
            await asyncio.sleep(2 ** attempt)

        logger.error("Email send failed after retries: %s", last_error)
        return {
            "status": "failed",
            "error_message": str(last_error)[:500] if last_error else "unknown",
        }

    async def send_document_extraction(
        self,
        business_name: str,
        extracted_data: Optional[dict],
        low_confidence_fields: Optional[dict] = None,
        status: str = "extracted",
        source_label: str = "",
    ) -> dict:
        """Build the extraction email HTML and send it to the demo notify address."""
        html = build_extraction_email_html(
            business_name=business_name,
            extracted_data=extracted_data,
            status=status,
            low_confidence_fields=low_confidence_fields,
            source_label=source_label,
        )
        subject = f"Documento Extraido - {business_name or 'Negocio'}"
        text = f"Extracao de documento para {business_name or 'negocio'}. Estado: {status}."
        return await self.send_email(
            to=self.notify_email,
            subject=subject,
            html_body=html,
            text_body=text,
        )


resend_emailer = ResendEmailer()
