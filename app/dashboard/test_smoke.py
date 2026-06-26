"""Smoke tests for the dashboard UI router.

Run in an environment with fastapi + httpx installed, e.g.:

    pytest app/dashboard/test_smoke.py -q

These tests do NOT start LiveKit, WhatsApp, or any external service. They only
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
    "/api/scenarios/niches",
    "/api/scenarios/build",
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


def test_livekit_cdn_referenced():
    html = _INDEX.read_text(encoding="utf-8")
    assert "cdn.jsdelivr.net/npm/livekit-client" in html
    assert "LivekitClient" in html


def test_static_route_serves_index_and_404s_missing():
    client = TestClient(_app())
    r = client.get("/static/index.html")
    assert r.status_code == 200
    assert "AutoPME Demo Studio" in r.text
    missing = client.get("/static/nao_existe.xyz")
    assert missing.status_code == 404


def test_transcript_data_channel_handler_present():
    """Confirma que o JS subscreve o data channel para transcrição ao vivo."""
    html = _INDEX.read_text(encoding="utf-8")
    assert "RoomEvent.DataReceived" in html
    assert '"transcript"' in html or "'transcript'" in html
