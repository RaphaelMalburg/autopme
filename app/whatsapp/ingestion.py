"""Document ingestion pipeline for the WhatsApp module.

Portado de agente-consultoria/app/services/document_extractor.py, adaptado para
receber bytes raw (upload multipart ou media do gateway Baileys) em vez de file URLs.

Fluxo:
- PDF: extrai texto com pypdf (lazy import; fallback para vision se vazio/indisponivel).
- Imagem (jpg/png/webp/heic/...): base64 -> data URL -> extracao vision (gemini multimodal).
- Devolve dados estruturados + scores de confianca + campos de baixa confianca.

pypdf e opcional: se nao estiver instalado, a extracao de texto de PDF falha
graciosamente e recai sobre o modelo vision (que tambem aceita PDFs).
"""
from __future__ import annotations

import io
import logging
import mimetypes
from typing import Optional

from app.whatsapp.openrouter_vision import (
    OpenRouterVisionError,
    build_data_url,
    openrouter_vision,
)

logger = logging.getLogger(__name__)

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tiff", ".tif")


def is_pdf(mimetype: str, filename: str) -> bool:
    mt = (mimetype or "").lower()
    name = (filename or "").lower()
    return mt == "application/pdf" or name.endswith(".pdf")


def is_image(mimetype: str, filename: str) -> bool:
    mt = (mimetype or "").lower()
    name = (filename or "").lower()
    if mt.startswith("image/"):
        return True
    return any(name.endswith(ext) for ext in _IMAGE_EXTS)


def guess_mimetype(filename: str, mimetype: Optional[str] = None) -> str:
    if mimetype:
        return mimetype
    guessed = mimetypes.guess_type(filename or "")[0]
    return guessed or "application/octet-stream"


def _filename_from_mimetype(mimetype: str) -> str:
    ext = mimetypes.guess_extension(mimetype or "") or ""
    return f"documento{ext}"


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF bytes using pypdf (lazy import). Returns '' if unavailable."""
    try:
        from pypdf import PdfReader
    except Exception as e:  # not installed / import error
        logger.warning("pypdf not available, cannot extract PDF text: %s", e)
        return ""
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages).strip()
    except Exception as e:
        logger.error("PDF text extraction failed: %s", e)
        return ""


async def extract_document(
    content: bytes,
    filename: str,
    mimetype: Optional[str] = None,
    prospect_context: str = "",
    language: str = "pt",
) -> dict:
    """Extract structured data from a document (image or PDF bytes).

    Returns a dict with shape::

        {
            "status": "extracted" | "extracted_with_warnings" | "extraction_failed",
            "extracted": {...} | None,          # parsed business data
            "confidence_scores": {...},
            "low_confidence_fields": {...},
            "raw_text": str | None,             # present when JSON parse failed
            "error": str | None,                # present on failure
        }
    """
    mimetype = guess_mimetype(filename, mimetype)
    prospect_context = prospect_context or ""

    try:
        if is_pdf(mimetype, filename):
            pdf_text = _extract_pdf_text(content)
            if not pdf_text:
                logger.info("PDF text empty/unavailable, falling back to vision extraction")
                data_url = build_data_url(content, mimetype)
                result = await openrouter_vision.extract_from_image(
                    data_url=data_url, prospect_context=prospect_context, language=language
                )
            else:
                result = await openrouter_vision.extract_from_text(
                    text=pdf_text, prospect_context=prospect_context, language=language
                )
        elif is_image(mimetype, filename):
            data_url = build_data_url(content, mimetype)
            result = await openrouter_vision.extract_from_image(
                data_url=data_url, prospect_context=prospect_context, language=language
            )
        else:
            # Unknown type: attempt vision extraction via data URL anyway.
            logger.info("Unsupported mimetype %s, attempting vision extraction", mimetype)
            data_url = build_data_url(content, mimetype)
            result = await openrouter_vision.extract_from_image(
                data_url=data_url, prospect_context=prospect_context, language=language
            )

        extracted_data = result.get("extracted_data")
        if extracted_data is None:
            return {
                "status": "extraction_failed",
                "extracted": None,
                "confidence_scores": result.get("confidence_scores", {}),
                "low_confidence_fields": result.get("low_confidence_fields", {}),
                "raw_text": result.get("raw_text"),
                "error": None,
            }

        low_confidence = result.get("low_confidence_fields", {})
        status = "extracted_with_warnings" if low_confidence else "extracted"
        return {
            "status": status,
            "extracted": extracted_data,
            "confidence_scores": result.get("confidence_scores", {}),
            "low_confidence_fields": low_confidence,
            "raw_text": None,
            "error": None,
        }

    except OpenRouterVisionError as e:
        logger.error("Document extraction LLM error: %s", e)
        return {
            "status": "extraction_failed",
            "extracted": None,
            "confidence_scores": {},
            "low_confidence_fields": {},
            "raw_text": None,
            "error": str(e),
        }
    except Exception as e:
        logger.error("Document extraction unexpected error: %s", e)
        return {
            "status": "extraction_failed",
            "extracted": None,
            "confidence_scores": {},
            "low_confidence_fields": {},
            "raw_text": None,
            "error": str(e),
        }


async def ingest(
    content: bytes,
    filename: str,
    mimetype: Optional[str] = None,
    business_name: str = "",
    prospect_context: str = "",
    language: str = "pt",
) -> dict:
    """High-level convenience wrapper that builds prospect context then extracts."""
    if not prospect_context and business_name:
        prospect_context = f"Nome do negocio: {business_name}"
    return await extract_document(
        content=content,
        filename=filename,
        mimetype=mimetype,
        prospect_context=prospect_context,
        language=language,
    )
