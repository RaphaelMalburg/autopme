"""Testa que o KIT (docs/kit) funciona com o sistema real.

- Cada preset de nicho carrega via build_scenario sem erros e produz um
  system_prompt utilizavel com o conhecimento do negocio.
- O nicho de cada preset existe no sistema.
- templates.json e valido e bem formado.
- build_commercial_brief corre para cada nicho do preset.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.advisor.service import build_commercial_brief
from app.scenarios.builder import build_scenario
from app.scenarios.niches import get_niche_config

_KIT = Path(__file__).resolve().parents[2] / "docs" / "kit"
_PRESETS = sorted((_KIT / "presets").glob("*.json"))
_VALID_TEMPLATE_CATEGORIES = {"UTILITY", "MARKETING", "AUTHENTICATION"}


def test_presets_exist():
    assert _PRESETS, "Nenhum preset encontrado em docs/kit/presets"
    assert len(_PRESETS) >= 11, f"Esperados >=11 presets, encontrados {len(_PRESETS)}"


@pytest.mark.parametrize("preset_path", _PRESETS, ids=lambda p: p.stem)
def test_preset_loads_into_scenario(preset_path: Path):
    data = json.loads(preset_path.read_text(encoding="utf-8"))

    # estrutura minima
    for key in ("niche", "business_name", "language", "extra"):
        assert key in data, f"{preset_path.name} sem chave '{key}'"

    niche = data["niche"]
    assert get_niche_config(niche) is not None, f"Nicho invalido no sistema: {niche}"

    # o ficheiro deve chamar-se como o nicho (organizacao)
    assert preset_path.stem == niche, f"{preset_path.name} deveria chamar-se {niche}.json"

    scenario = build_scenario(
        niche,
        data["business_name"],
        extra=data.get("extra") or None,
        language=data.get("language") or "pt-PT",
        free_context=data.get("free_context") or "",
    )
    sp = scenario["system_prompt"]
    assert sp and len(sp) > 100, "system_prompt vazio/curto"
    assert data["business_name"] in sp, "system_prompt nao contem o nome do negocio"
    # o conhecimento (extra) deve estar refletido no prompt
    assert scenario.get("first_message_inbound"), "sem mensagem de abertura inbound"


@pytest.mark.parametrize("preset_path", _PRESETS, ids=lambda p: p.stem)
def test_advisor_brief_for_preset_niche(preset_path: Path):
    data = json.loads(preset_path.read_text(encoding="utf-8"))
    brief = build_commercial_brief(
        {
            "business_name": data["business_name"],
            "niche": data["niche"],
            "extra": data.get("extra"),
            "roi": {
                "consultations_per_day": 20,
                "current_no_show_rate": 15,
                "target_no_show_rate": 5,
                "revenue_per_consultation": 50,
                "monthly_gain": 2000,
            },
        }
    )
    assert brief["detected_pains"], "diagnostico sem dores"
    assert brief["quick_wins"], "diagnostico sem quick wins"
    assert brief["export_markdown"], "diagnostico sem export"


def test_embedded_presets_match_docs():
    """app/scenarios/presets.py (canonico) tem de bater certo com docs/kit/presets/*.json."""
    from app.scenarios.presets import NICHE_PRESETS

    docs = {}
    for p in _PRESETS:
        d = json.loads(p.read_text(encoding="utf-8"))
        docs[d["niche"]] = d
    assert set(NICHE_PRESETS.keys()) == set(docs.keys()), "presets embutidos != docs"
    for niche, data in docs.items():
        assert NICHE_PRESETS[niche] == data, f"preset '{niche}' divergente entre app e docs"


def test_whatsapp_templates_json_valid():
    path = _KIT / "whatsapp" / "templates.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    templates = data.get("templates")
    assert templates and len(templates) >= 6, "esperados >=6 templates"
    names = set()
    for t in templates:
        assert t.get("name"), "template sem nome"
        assert t["name"] not in names, f"nome de template duplicado: {t['name']}"
        names.add(t["name"])
        assert t.get("category") in _VALID_TEMPLATE_CATEGORIES, f"categoria invalida: {t.get('category')}"
        bodies = [c for c in t.get("components", []) if c.get("type") == "BODY"]
        assert bodies, f"template {t['name']} sem BODY"
        assert bodies[0].get("text"), f"template {t['name']} com BODY vazio"
