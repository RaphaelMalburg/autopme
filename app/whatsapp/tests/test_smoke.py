"""Smoke test for app.whatsapp ingestion + emailer logic (no network).

Run from the worktree root:
    python app/whatsapp/tests/test_smoke.py

Mocks OpenRouter (call_llm) and Resend (send_email) so no real HTTP is made.
Validates: image ingestion, PDF fallback ingestion, email HTML builder, email
send path, JID normalization, and ingestion type helpers.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add worktree root to sys.path so `import app...` works when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def main() -> int:
    from app.whatsapp import openrouter_vision as ov
    from app.whatsapp import ingestion as ing
    from app.whatsapp import emailer as em
    from app.whatsapp import client as cl

    failures: list[str] = []

    def check(label: str, cond: bool) -> None:
        if cond:
            print(f"  PASS: {label}")
        else:
            print(f"  FAIL: {label}")
            failures.append(label)

    canned = json.dumps(
        {
            "nome_negocio": "Clinica Exemplo",
            "contacto_telefone": "+351912345678",
            "contacto_email": "info@clinica.pt",
            "morada": "Rua das Flores 1, Porto",
            "servicos": ["Limpeza", "Ortodontia"],
            "horario_funcionamento": "Seg-Sex 9h-18h",
            "precos": [{"servico": "Limpeza", "preco": "50 EUR"}],
            "observacoes": "Aceita convenios",
            "confianca": {
                "nome_negocio": 0.9,
                "contacto_telefone": 0.7,
                "contacto_email": 0.95,
                "morada": 0.6,
                "servicos": 0.9,
                "horario_funcionamento": 0.85,
                "precos": 0.5,
                "observacoes": 0.8,
            },
        },
        ensure_ascii=False,
    )

    # --- Mocks at the network boundary (no real HTTP) ---
    async def fake_call_llm(messages, model=None, json_mode=False, temperature=0.2, max_tokens=2000):
        return canned

    async def fake_send_email(to, subject, html_body, text_body=""):
        return {
            "status": "sent",
            "resend_message_id": "mock-id",
            "sent_at": "2026-01-01T00:00:00+00:00",
        }

    ov.openrouter_vision.call_llm = fake_call_llm
    em.resend_emailer.send_email = fake_send_email

    async def run() -> None:
        # 1) Image ingestion
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
        res = await ing.extract_document(
            content=fake_png,
            filename="menu.png",
            mimetype="image/png",
            prospect_context="Nome do negocio: Clinica Exemplo",
        )
        extracted1 = res.get("extracted")
        check("image ingestion returns extracted dict", isinstance(extracted1, dict))
        check(
            "image extraction nome_negocio",
            (extracted1 or {}).get("nome_negocio") == "Clinica Exemplo",
        )
        check(
            "image extraction status is extracted_with_warnings (low-conf fields exist)",
            res.get("status") == "extracted_with_warnings",
        )
        check(
            "image extraction has low_confidence_fields",
            isinstance(res.get("low_confidence_fields"), dict)
            and len(res["low_confidence_fields"]) > 0,
        )

        # 2) PDF ingestion -> pypdf not installed -> fallback to vision
        fake_pdf = b"%PDF-1.4\n%fake pdf\n" + b"\x00" * 32
        res2 = await ing.extract_document(
            content=fake_pdf,
            filename="doc.pdf",
            mimetype="application/pdf",
            prospect_context="",
        )
        extracted2 = res2.get("extracted")
        check("pdf fallback returns extracted dict", isinstance(extracted2, dict))
        check(
            "pdf fallback nome_negocio",
            (extracted2 or {}).get("nome_negocio") == "Clinica Exemplo",
        )

        # 3) Email HTML builder (pure, no network)
        html = em.build_extraction_email_html(
            business_name="Clinica Exemplo",
            extracted_data=extracted1,
            status="extracted_with_warnings",
            low_confidence_fields=res["low_confidence_fields"],
            source_label="Upload dashboard: menu.png",
        )
        check("email html contains business name", "Clinica Exemplo" in html)
        check("email html contains a field key", "nome_negocio" in html)
        check("email html contains warnings section", "baixa confianca" in html)
        check("email html is escaped (no raw <script>)", "<script>" not in html)

        # 4) Email send path via mocked send_email through send_document_extraction
        sent = await em.resend_emailer.send_document_extraction(
            business_name="Clinica Exemplo",
            extracted_data=extracted1,
            low_confidence_fields=res["low_confidence_fields"],
            status="extracted_with_warnings",
            source_label="test",
        )
        check("email send returns status sent", sent.get("status") == "sent")

        # 5) JID normalization
        check(
            "jid normalizes bare digits",
            cl._normalize_jid("351912345678") == "351912345678@s.whatsapp.com",
        )
        check(
            "jid keeps existing jid",
            cl._normalize_jid("351912345678@s.whatsapp.com")
            == "351912345678@s.whatsapp.com",
        )
        check(
            "jid strips non-digits",
            cl._normalize_jid("+351 912 345 678") == "351912345678@s.whatsapp.com",
        )

        # 6) ingestion type helpers
        check("is_pdf by mimetype", ing.is_pdf("application/pdf", "x") is True)
        check("is_pdf by filename", ing.is_pdf("", "menu.pdf") is True)
        check("is_image by mimetype", ing.is_image("image/png", "x") is True)
        check("is_image by extension", ing.is_image("", "photo.jpg") is True)

    asyncio.run(run())

    if failures:
        print(f"\n{len(failures)} FAILED: {failures}")
        return 1
    print("\nAll smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
