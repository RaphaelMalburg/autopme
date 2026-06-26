"""Pesquisa de prospect na web via OpenRouter (plugin `web`).

Fluxo:
- Recebe uma query (nome do negocio + localizacao/website, ex.: "Clinica Dentaria
  Sorriso Porto") e um niche_hint opcional.
- Chama o OpenRouter com o plugin `web` (pesquisa Google via Exa, ~$0.005/pesquisa,
  chave ja existente — sem novo registo).
- O modelo pesquisa, le os resultados e devolve JSON estruturado com os dados do
  negocio + um objeto `scenario_extra` pronto a alimentar o construtor de cenarios.

So depende de httpx (via app.whatsapp.openrouter_vision) + app.scenarios.niches.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from app.whatsapp.openrouter_vision import OpenRouterVisionError, openrouter_vision
from app.scenarios.niches import NICHE_ORDER

logger = logging.getLogger(__name__)

_RESEARCH_SYSTEM = (
    "Es um assistente que pesquisa negocios reais na web para preparar demonstracoes "
    "de vendas para a AutoPME. Usas os resultados da pesquisa web para extrair informacoes "
    "fatuais sobre o negocio pedido. Responde em portugues europeu. Se nao encontrares "
    "informacao para um campo, usa null — nunca inventes dados."
)

_RESEARCH_PROMPT = """Pesquisa na web informacoes sobre o seguinte negocio e extrai os dados estruturados em JSON.

Pesquisa: {query}
Nicho sugerido (pode ser ignorado se nao for o correto): {niche_hint}

Nichos validos para o campo "niche": {niches}

Extrai os seguintes campos (quando disponiveis; usa null se nao encontrares):
- nome_negocio (string)
- niche (string, um de: {niches})
- morada (string)
- telefone (string)
- website (string)
- opening_hours (string resumida, ex.: "Seg-Sex 9h-19h, Sab 9h-13h")
- services (lista de strings)
- prices (lista de strings no formato "servico: preco")
- notes (string com observacoes uteis: estacionamento, convenios, acessibilidade, etc.)

Adicionalmente, inclui um objeto "scenario_extra" com estes campos ja formatados em texto curto para alimentar diretamente o construtor de cenarios:
- scenario_extra.opening_hours (string)
- scenario_extra.services (string, itens separados por virgula)
- scenario_extra.prices (string, itens separados por virgula)
- scenario_extra.notes (string)

Responde APENAS com JSON valido, sem markdown, sem texto antes ou depois do JSON."""


def _strip_json_fences(raw: str) -> str:
    """Remove ```json ... ``` fences e espacos envolventes, se presentes."""
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _safe_parse(raw: str) -> dict[str, Any]:
    """Parse JSON tolerante a fences/markdown. Devolve {} se impossivel."""
    cleaned = _strip_json_fences(raw)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        # tentar extrair o primeiro bloco {...}
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    logger.warning("research_prospect: resposta nao-JSON, devolvendo raw_text")
    return {}


async def research_prospect(query: str, niche_hint: Optional[str] = None) -> dict[str, Any]:
    """Pesquisa um prospect na web e devolve dados estruturados + `extra`.

    Returns:
        {
          "query": str,
          "extracted": {...},        # dados do negocio (sem scenario_extra)
          "extra": {...},            # opening_hours/services/prices/notes para o scenario builder
          "niche_guess": str | None, # niche detetado (um de NICHE_ORDER) ou None
          "raw_text": str | None,    # presente se o parse JSON falhou
        }
    """
    niches = ", ".join(NICHE_ORDER)
    prompt = _RESEARCH_PROMPT.format(
        query=query,
        niche_hint=niche_hint or "(nao indicado)",
        niches=niches,
    )
    messages = [
        {"role": "system", "content": _RESEARCH_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    # Plugin `web` do OpenRouter: pesquisa Google via Exa, uma vez por pedido.
    # Usa a chave ja existente (custo ~$0.005/pesquisa).
    plugins = [{"id": "web", "max_results": 5}]
    try:
        raw = await openrouter_vision.call_llm(
            messages,
            json_mode=True,
            temperature=0.2,
            max_tokens=2000,
            plugins=plugins,
        )
    except OpenRouterVisionError as e:
        logger.error("research_prospect OpenRouter error: %s", e)
        return {
            "query": query,
            "extracted": None,
            "extra": {},
            "niche_guess": None,
            "error": str(e),
        }

    data = _safe_parse(raw)
    if not data:
        return {
            "query": query,
            "extracted": None,
            "extra": {},
            "niche_guess": None,
            "raw_text": raw,
        }

    extra = data.get("scenario_extra")
    if not isinstance(extra, dict):
        extra = {}

    # Garantir que o extra tem so as chaves esperadas pelo builder.
    extra_clean = {
        "opening_hours": str(extra.get("opening_hours") or "").strip(),
        "services": str(extra.get("services") or "").strip(),
        "prices": str(extra.get("prices") or "").strip(),
        "notes": str(extra.get("notes") or "").strip(),
    }

    extracted = {k: v for k, v in data.items() if k != "scenario_extra"}
    niche_guess = extracted.get("niche")
    if niche_guess and niche_guess not in NICHE_ORDER:
        niche_guess = None

    return {
        "query": query,
        "extracted": extracted,
        "extra": extra_clean,
        "niche_guess": niche_guess,
    }
