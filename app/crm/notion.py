"""Notion CRM integration — push a demo prospect into the AutoPME Pipeline.

Liga o demo-studio a Pipeline de Clientes do Notion: ao fim de uma demo, o
diagnostico comercial (advisor) cria/atualiza o cartao do prospect no funil.

Design:
- `build_pipeline_properties` e PURO (sem rede), por isso e testavel offline.
- `create_pipeline_page` faz a chamada HTTP a API do Notion (httpx).

Configuracao (ver .env.example):
- NOTION_TOKEN: token de uma integracao interna do Notion partilhada com a
  base "Pipeline de Clientes".
- NOTION_PIPELINE_DATABASE_ID: id da database Pipeline de Clientes.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

# Estados validos da coluna "Estado" na Pipeline do Notion.
DEFAULT_STATE = "🟠 Em conversa"

# Pacotes validos da coluna "Pacote interesse".
VALID_PACKAGES = {"Arranque", "Base", "Crescimento"}

# Nichos do codigo (chaves internas) -> opcoes existentes no select "Nicho" do
# Notion. Nichos sem correspondencia (restaurant/bakery/beauty/...) ficam sem
# select (vao para as Notas) para nao poluir o schema com opcoes novas.
NICHE_TO_NOTION = {
    "dental": "Clínica Dentária",
    "legal": "Advocacia",
    "accounting": "Contabilidade",
    "automotive": "Oficina Mecânica",
    "real_estate": "Imobiliária",
    "fitness": "Ginásio/Estúdio",
    "pharmacy": "Farmácia",
}


def _rich_text(value: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": value[:2000]}}]}


def _notas_from_brief(brief: dict[str, Any]) -> str:
    """Resumo executivo + quick wins, formatado para o campo Notas."""
    parts: list[str] = []
    summary = (brief.get("executive_summary") or "").strip()
    if summary:
        parts.append(summary)
    wins = [str(w).strip() for w in (brief.get("quick_wins") or []) if str(w).strip()]
    if wins:
        parts.append("Quick wins: " + "; ".join(wins))
    pains = [str(p).strip() for p in (brief.get("detected_pains") or []) if str(p).strip()]
    if pains:
        parts.append("Dores: " + "; ".join(pains[:3]))
    return "\n".join(parts)


def build_pipeline_properties(
    brief: dict[str, Any],
    *,
    email: str = "",
    phone: str = "",
    address: str = "",
    state: str = DEFAULT_STATE,
    package: str = "",
    setup_value: Optional[float] = None,
    retainer_value: Optional[float] = None,
    next_contact_date: str = "",
) -> dict[str, Any]:
    """Mapeia o brief do advisor + dados de contacto para propriedades do Notion.

    Funcao pura: nao faz rede. So inclui propriedades com valor, para nao
    sobrescrever campos no Notion com vazios.
    """
    business_name = (brief.get("business_name") or "Negocio").strip() or "Negocio"
    snapshot = brief.get("extracted_snapshot") or {}

    props: dict[str, Any] = {
        "Nome da Empresa": {"title": [{"text": {"content": business_name[:200]}}]},
        "Estado": {"select": {"name": state or DEFAULT_STATE}},
    }

    notas = _notas_from_brief(brief)
    if notas:
        props["Notas"] = _rich_text(notas)

    niche = str(brief.get("niche") or "")
    notion_niche = NICHE_TO_NOTION.get(niche)
    if notion_niche:
        props["Nicho"] = {"select": {"name": notion_niche}}
    elif notas and niche:
        # nicho sem opcao no Notion: anexa o label as notas
        label = brief.get("niche_label") or niche
        props["Notas"] = _rich_text(f"[{label}]\n{notas}")

    email = (email or "").strip()
    if email:
        props["Email"] = {"email": email}

    phone = (phone or snapshot.get("phone") or "").strip()
    if phone:
        props["Telefone"] = _rich_text(phone)

    address = (address or "").strip()
    if address:
        props["Morada"] = _rich_text(address)

    if package and package in VALID_PACKAGES:
        props["Pacote interesse"] = {"select": {"name": package}}

    if setup_value is not None:
        props["Valor setup €"] = {"number": float(setup_value)}
    if retainer_value is not None:
        props["Retainer €/mês"] = {"number": float(retainer_value)}

    if next_contact_date:
        props["Próximo contacto"] = {"date": {"start": next_contact_date}}

    return props


async def create_pipeline_page(
    *,
    token: str,
    database_id: str,
    properties: dict[str, Any],
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Cria uma pagina (cartao) na database Pipeline do Notion.

    Devolve {"ok": True, "page_id": ..., "url": ...} ou levanta httpx.HTTPStatusError.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    body = {"parent": {"database_id": database_id}, "properties": properties}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(NOTION_API_URL, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return {"ok": True, "page_id": data.get("id", ""), "url": data.get("url", "")}
