from app.crm.notion import (
    DEFAULT_STATE,
    NICHE_TO_NOTION,
    build_pipeline_properties,
    suggest_package,
)


def test_suggest_package_thresholds():
    assert suggest_package(500)["package"] == "Arranque"
    assert suggest_package(2000)["package"] == "Base"
    assert suggest_package(5000)["package"] == "Crescimento"
    # valores coerentes e crescentes
    assert suggest_package(5000)["setup_value"] > suggest_package(500)["setup_value"]
    assert suggest_package(2000)["retainer_value"] >= suggest_package(500)["retainer_value"]


def _brief(niche: str = "dental") -> dict:
    return {
        "business_name": "Clinica Exemplo",
        "niche": niche,
        "niche_label": "clinica dentaria",
        "executive_summary": "a Clinica Exemplo pode ganhar velocidade comercial",
        "quick_wins": ["confirmacao automatica de consultas", "agente de voz"],
        "detected_pains": ["chamadas perdidas", "no-shows altos"],
        "extracted_snapshot": {"phone": "+351 912 000 000"},
    }


def test_maps_known_niche_to_notion_select():
    props = build_pipeline_properties(_brief("dental"))
    assert props["Nicho"]["select"]["name"] == NICHE_TO_NOTION["dental"]
    assert props["Nome da Empresa"]["title"][0]["text"]["content"] == "Clinica Exemplo"
    assert props["Estado"]["select"]["name"] == DEFAULT_STATE
    assert "Quick wins" in props["Notas"]["rich_text"][0]["text"]["content"]


def test_unknown_niche_has_no_select_but_label_in_notas():
    props = build_pipeline_properties(_brief("restaurant"))
    assert "Nicho" not in props
    assert props["Notas"]["rich_text"][0]["text"]["content"].startswith("[")


def test_only_includes_provided_fields():
    props = build_pipeline_properties(_brief(), email="x@y.com", setup_value=600)
    assert props["Email"]["email"] == "x@y.com"
    assert props["Valor setup €"]["number"] == 600.0
    # campos nao fornecidos nao aparecem
    assert "Morada" not in props
    assert "Retainer €/mês" not in props


def test_invalid_package_is_dropped():
    props = build_pipeline_properties(_brief(), package="Invalido")
    assert "Pacote interesse" not in props
    props2 = build_pipeline_properties(_brief(), package="Base")
    assert props2["Pacote interesse"]["select"]["name"] == "Base"


def test_phone_falls_back_to_snapshot():
    props = build_pipeline_properties(_brief())
    assert props["Telefone"]["rich_text"][0]["text"]["content"] == "+351 912 000 000"
