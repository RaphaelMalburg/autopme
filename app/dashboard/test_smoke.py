"""Smoke tests for the dashboard UI router.

Run in an environment with fastapi + httpx installed, e.g.:

    pytest app/dashboard/test_smoke.py -q

These tests do NOT start WhatsApp, Vapi, or any external service. They only
verify that the router serves the single-page UI and that the JS references the
shared API endpoints from the contract.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard import dashboard_router

_STATIC = Path(__file__).resolve().parent / "static"
_INDEX = _STATIC / "index.html"

_SCENARIO_LABELS = [
    "Voz Inbound",
    "Voz Outbound",
    "WhatsApp FAQ",
    "Ingestão de Documentos",
    "Reativação de Inativos",
    "Calculadora de ROI",
]

_CONTRACT_ENDPOINTS = [
    "/api/auth/login",
    "/api/scenarios/niches",
    "/api/scenarios/build",
    "/api/advisor/brief",
    "/api/voice/call/start",
    "/api/whatsapp/qr",
    "/api/whatsapp/send",
    "/api/whatsapp/ingest",
]


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(dashboard_router)
    return app


def test_index_html_exists():
    assert _INDEX.is_file(), "index.html em falta no diretório static"


def test_index_served_at_root():
    client = TestClient(_app())
    r = client.get("/")
    assert r.status_code == 200
    assert "AutoPME Demo Studio" in r.text
    for label in _SCENARIO_LABELS:
        assert label in r.text, f"cenário em falta no HTML: {label}"


def test_js_references_contract_endpoints():
    html = _INDEX.read_text(encoding="utf-8")
    for ep in _CONTRACT_ENDPOINTS:
        assert ep in html, f"endpoint do contrato em falta no JS: {ep}"


def test_vapi_sdk_referenced():
    html = _INDEX.read_text(encoding="utf-8")
    assert "@vapi-ai/web" in html
    assert "new Vapi(" in html


def test_static_route_serves_index_and_404s_missing():
    client = TestClient(_app())
    r = client.get("/static/index.html")
    assert r.status_code == 200
    assert "AutoPME Demo Studio" in r.text
    missing = client.get("/static/nao_existe.xyz")
    assert missing.status_code == 404


def test_browser_and_vapi_transcript_handlers_present():
    """Confirma que o JS trata transcrição ao vivo nos modos browser e Vapi."""
    html = _INDEX.read_text(encoding="utf-8")
    assert "appendTranscript(" in html
    assert 'msg.type === "transcript"' in html or "msg.type === 'transcript'" in html
