"""Testes do agente conversacional de WhatsApp (sem chamadas LLM reais)."""
import asyncio
import importlib


def _setup(tmp_path, monkeypatch):
    """Aponta o storage para um tmp isolado e devolve o modulo agent recarregado."""
    from app.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    from app.storage import db as db_module

    importlib.reload(db_module)
    db_module.init_db()

    from app.whatsapp import agent as agent_module

    importlib.reload(agent_module)
    return agent_module


def test_help_and_reset_commands(tmp_path, monkeypatch):
    agent = _setup(tmp_path, monkeypatch)
    agent.set_active_scenario("dental", "Clinica Sorriso", language="pt-PT")

    reply = asyncio.run(agent.handle_text_message("351900000000", "ajuda"))
    assert "Clinica Sorriso" in reply

    reply = asyncio.run(agent.handle_text_message("351900000000", "reiniciar"))
    assert "reiniciada" in reply.lower()


def test_no_active_scenario_returns_safe_fallback(tmp_path, monkeypatch):
    agent = _setup(tmp_path, monkeypatch)
    reply = asyncio.run(agent.handle_text_message("351900000000", "Qual o horario?"))
    assert "documento" in reply.lower() or "contacto" in reply.lower()


def test_llm_reply_persists_history(tmp_path, monkeypatch):
    agent = _setup(tmp_path, monkeypatch)
    agent.set_active_scenario("dental", "Clinica Sorriso", language="pt-PT")

    async def fake_chat_turn(system_prompt, history, user_message):
        assert "Clinica Sorriso" in system_prompt
        return "Estamos abertos de segunda a sexta, das 9h as 18h."

    monkeypatch.setattr(agent, "chat_turn", fake_chat_turn)

    reply = asyncio.run(agent.handle_text_message("351900000000", "Qual o horario?"))
    assert "9h" in reply

    # historico persistido: pergunta do user + resposta do agente
    hist = agent.db.wa_get_history("351900000000")
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert hist[1]["role"] == "assistant"


def test_get_active_scenario_roundtrip(tmp_path, monkeypatch):
    agent = _setup(tmp_path, monkeypatch)
    agent.set_active_scenario("legal", "Advogados XYZ", language="pt-PT", extra={"notes": "x"})
    active = agent.get_active_scenario()
    assert active["niche"] == "legal"
    assert active["business_name"] == "Advogados XYZ"
