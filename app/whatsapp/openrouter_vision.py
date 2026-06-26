"""OpenRouter vision client (httpx) for document extraction.

Portado de agente-consultoria/app/services/openrouter.py, adaptado para o modulo
WhatsApp. Usa o modelo multimodal google/gemini-2.5-flash via OpenRouter, enviando
imagens/PDFs como data URLs (base64) num content block ``image_url``.

So depende de httpx + app.config (NAO usa o SDK resend/openrouter).
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterVisionError(Exception):
    """Raised when the OpenRouter call fails after retries or auth is invalid."""


def build_data_url(content: bytes, mimetype: str) -> str:
    """Encode raw bytes as a ``data:<mime>;base64,...`` URL for OpenRouter image_url."""
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mimetype};base64,{encoded}"


def _parse_extraction(raw: str) -> dict:
    """Parse the LLM JSON response into the standard extraction result shape."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("OpenRouter returned invalid JSON for document extraction")
        return {
            "extracted_data": None,
            "raw_text": raw,
            "confidence_scores": {},
            "low_confidence_fields": {},
        }
    confidence = parsed.get("confianca", {})
    if not isinstance(confidence, dict):
        confidence = {}
    low_confidence = {
        k: v for k, v in confidence.items()
        if isinstance(v, (int, float)) and v < 0.8
    }
    return {
        "extracted_data": parsed,
        "confidence_scores": confidence,
        "low_confidence_fields": low_confidence,
    }


_EXTRACTION_PROMPT = """Analisa este documento comercial e extrai os dados estruturados em JSON.

Contexto do negocio:
{context}

Extrai os seguintes campos (quando disponiveis):
- nome_negocio
- contacto_telefone
- contacto_email
- morada
- servicos (lista)
- horario_funcionamento
- precos (lista de servico/preco)
- observacoes

Responde APENAS com JSON valido. Para campos nao encontrados, usa null.
Adiciona um campo "confianca" (0.0 a 1.0) para cada campo extraido."""


class OpenRouterVisionClient:
    """Async client for OpenRouter chat/completions with vision (image_url) support."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.default_model = settings.openrouter_default_model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://autopme.demo",
        }

    async def call_llm(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        plugins: Optional[list[dict]] = None,
    ) -> str:
        """POST to OpenRouter chat/completions and return the assistant message content.

        ``plugins`` ativa extensoes do OpenRouter (ex.: web search via
        ``[{"id": "web", "max_results": 5}]``) usando a mesma chave — sem novo registo.
        """
        model = model or self.default_model
        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if plugins:
            payload["plugins"] = plugins

        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers=self._headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info("OpenRouter call success: model=%s", model)
                    return content
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("OpenRouter timeout (attempt %d/3)", attempt + 1)
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise OpenRouterVisionError("Invalid OpenRouter API key")
                last_error = e
                logger.warning(
                    "OpenRouter HTTP %d (attempt %d/3)",
                    e.response.status_code,
                    attempt + 1,
                )
                await asyncio.sleep(2 ** attempt)
            except Exception as e:  # network errors, JSON errors, etc.
                last_error = e
                logger.error("OpenRouter unexpected error: %s", type(e).__name__)
                await asyncio.sleep(2 ** attempt)

        raise OpenRouterVisionError(f"OpenRouter failed after 3 attempts: {last_error}")

    async def extract_from_image(
        self,
        data_url: str,
        prospect_context: str = "",
        language: str = "pt",
    ) -> dict:
        """Vision extraction: image/PDF as a data URL -> structured JSON."""
        lang = "portugues" if language == "pt" else language
        prompt = _EXTRACTION_PROMPT.format(context=prospect_context or "(nao fornecido)")
        messages = [
            {"role": "system", "content": f"Es um assistente de extracao de dados de documentos. Responde em {lang}."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ]
        raw = await self.call_llm(messages, json_mode=True, temperature=0.2)
        return _parse_extraction(raw)

    async def extract_from_text(
        self,
        text: str,
        prospect_context: str = "",
        language: str = "pt",
    ) -> dict:
        """Text extraction (e.g. PDF text) -> structured JSON."""
        if not text.strip():
            return {
                "extracted_data": None,
                "raw_text": "",
                "confidence_scores": {},
                "low_confidence_fields": {},
            }
        lang = "portugues" if language == "pt" else language
        prompt = (
            "Analisa o texto extraido de um documento comercial e extrai os dados "
            "estruturados em JSON.\n\n"
            f"Contexto do negocio:\n{prospect_context or '(nao fornecido)'}\n\n"
            f"Texto do documento:\n{text[:12000]}\n\n"
            "Extrai os seguintes campos (quando disponiveis):\n"
            "- nome_negocio\n- contacto_telefone\n- contacto_email\n- morada\n"
            "- servicos (lista)\n- horario_funcionamento\n- precos (lista de servico/preco)\n"
            "- observacoes\n\n"
            "Responde APENAS com JSON valido. Para campos nao encontrados, usa null.\n"
            'Adiciona um campo "confianca" (0.0 a 1.0) para cada campo extraido.'
        )
        messages = [
            {"role": "system", "content": f"Es um assistente de extracao de dados de documentos. Responde em {lang}."},
            {"role": "user", "content": prompt},
        ]
        raw = await self.call_llm(messages, json_mode=True, temperature=0.2)
        return _parse_extraction(raw)


openrouter_vision = OpenRouterVisionClient()
