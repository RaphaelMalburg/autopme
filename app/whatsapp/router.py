"""FastAPI router for WhatsApp: QR, send, gateway webhook, document ingestion.

Prefix /api/whatsapp. JSON. PT-PT nas respostas e emails (sem acentos, por
consistencia com app/prompts_pt_pt.py e app/config.py).
"""
from __future__ import annotations

import base64
import logging
import mimetypes

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.whatsapp.client import WhatsAppGatewayError, whatsapp_client
from app.whatsapp.emailer import build_extraction_email_html, resend_emailer
from app.whatsapp.ingestion import extract_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class SendRequest(BaseModel):
    to: str
    message: str


def _build_prospect_context(business_name: str, niche: str) -> str:
    parts = []
    if business_name:
        parts.append(f"Nome do negocio: {business_name}")
    if niche:
        parts.append(f"Nicho: {niche}")
    return "\n".join(parts)


def _filename_from_mimetype(mimetype: str) -> str:
    ext = mimetypes.guess_extension(mimetype or "") or ""
    return f"documento{ext}"


@router.get("/qr")
async def whatsapp_qr():
    """Return the current WhatsApp QR code and connection status from the gateway."""
    return await whatsapp_client.get_qr()


@router.post("/send")
async def whatsapp_send(body: SendRequest):
    """Send a WhatsApp text message via the Baileys gateway."""
    try:
        await whatsapp_client.send_text(to=body.to, message=body.message)
    except WhatsAppGatewayError as e:
        raise HTTPException(status_code=502, detail=f"gateway error: {e}")
    return {"ok": True}


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Receive forwarded incoming messages from the Baileys gateway.

    If the message has media, decode it, run document ingestion, email the result,
    and reply to the sender with a PT-PT confirmation. Reads the body as raw JSON
    (the gateway sends a ``from`` key, which is a Python reserved word).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    sender = payload.get("from", "")
    message = payload.get("message", "")
    has_media = bool(payload.get("hasMedia"))
    media_b64 = payload.get("mediaBase64")
    mimetype = payload.get("mimetype") or "application/octet-stream"
    filename = payload.get("filename") or _filename_from_mimetype(mimetype)

    logger.info("WhatsApp webhook: from=%s hasMedia=%s mimetype=%s", sender, has_media, mimetype)

    if not has_media or not media_b64:
        try:
            await whatsapp_client.send_text(
                to=sender,
                message=(
                    "Obrigado pela sua mensagem. Para extrairmos os dados do seu negocio, "
                    "envie-nos uma foto ou PDF do documento (ex.: menu, folheto, lista de precos)."
                ),
            )
        except WhatsAppGatewayError as e:
            logger.warning("Could not reply (no media) to %s: %s", sender, e)
        return {"status": "ok", "action": "no_media"}

    try:
        content = base64.b64decode(media_b64)
    except Exception as e:
        logger.error("Invalid mediaBase64: %s", e)
        return {"status": "error", "error": "invalid_media_base64"}

    result = await extract_document(
        content=content,
        filename=filename,
        mimetype=mimetype,
        prospect_context=message or "",
        language="pt",
    )

    extracted = result.get("extracted")
    business_name = (extracted or {}).get("nome_negocio") or "Negocio"
    status = result.get("status", "extraction_failed")

    email_result = await resend_emailer.send_document_extraction(
        business_name=business_name,
        extracted_data=extracted,
        low_confidence_fields=result.get("low_confidence_fields"),
        status=status,
        source_label=f"WhatsApp {sender}",
    )
    email_sent = email_result.get("status") == "sent"

    if extracted:
        reply = ("Recebemos o seu documento e extraimos os dados. "
                 "Enviamos um email com o resumo. Obrigado!")
    else:
        reply = ("Recebemos o seu documento, mas nao foi possivel extrair os dados "
                 "automaticamente. A equipa ira analisar e entrar em contacto.")
    try:
        await whatsapp_client.send_text(to=sender, message=reply)
    except WhatsAppGatewayError as e:
        logger.warning("Could not reply to %s: %s", sender, e)

    return {
        "status": "ok",
        "action": "ingested",
        "extracted": extracted,
        "email_sent": email_sent,
    }


@router.post("/ingest")
async def whatsapp_ingest(
    file: UploadFile = File(...),
    business_name: str = Form(""),
    niche: str = Form(""),
):
    """Ingest a document uploaded from the dashboard: extract -> email -> preview.

    Multipart form fields:
      - file:          the document (image or PDF)
      - business_name: optional business name hint (form field)
      - niche:         optional niche hint (form field)

    Returns (superset of the shared contract)::
        {
          "extracted": {...} | null,
          "email_sent": bool,
          "email_preview": "<html>",
          "status": "extracted" | "extracted_with_warnings" | "extraction_failed",
          "low_confidence_fields": {...},
          "filename": "..."
        }
    """
    content = await file.read()
    filename = file.filename or "documento"
    mimetype = file.content_type or "application/octet-stream"

    prospect_context = _build_prospect_context(business_name=business_name, niche=niche)

    result = await extract_document(
        content=content,
        filename=filename,
        mimetype=mimetype,
        prospect_context=prospect_context,
        language="pt",
    )

    extracted = result.get("extracted")
    resolved_name = (extracted or {}).get("nome_negocio") or business_name or "Negocio"
    status = result.get("status", "extraction_failed")

    email_html = build_extraction_email_html(
        business_name=resolved_name,
        extracted_data=extracted,
        status=status,
        low_confidence_fields=result.get("low_confidence_fields"),
        source_label=f"Upload dashboard: {filename}",
    )

    subject = f"Documento Extraido - {resolved_name}"
    email_result = await resend_emailer.send_email(
        to=resend_emailer.notify_email,
        subject=subject,
        html_body=email_html,
        text_body=f"Extracao de documento para {resolved_name}. Estado: {status}.",
    )
    email_sent = email_result.get("status") == "sent"

    return {
        "extracted": extracted,
        "email_sent": email_sent,
        "email_preview": email_html,
        "status": status,
        "low_confidence_fields": result.get("low_confidence_fields", {}),
        "filename": filename,
    }
