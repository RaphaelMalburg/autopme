"""Persistencia leve do demo-studio — historico de demos (stdlib sqlite3).

Filosofia do projeto: sem deps pesadas no control-plane. Usa o `sqlite3` da
biblioteca padrao, num ficheiro dentro de STORAGE_DIR (volume Railway em prod).

Guarda uma linha por diagnostico comercial gerado (uma "demo_session"), com o
ganho estimado, o nicho e se foi empurrado para a Pipeline do Notion. Isto da
historico e metricas reais de venda, em vez de demos efemeras.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _db_path() -> str:
    storage_dir = (settings.storage_dir or "./data").strip()
    os.makedirs(storage_dir, exist_ok=True)
    return os.path.join(storage_dir, "demo_studio.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    business_name TEXT,
    niche TEXT,
    niche_label TEXT,
    language TEXT,
    research_query TEXT,
    monthly_gain REAL DEFAULT 0,
    saved_slots REAL DEFAULT 0,
    executive_summary TEXT,
    pushed_to_notion INTEGER DEFAULT 0,
    notion_page_url TEXT,
    brief_json TEXT
);

CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS whatsapp_session (
    from_number TEXT PRIMARY KEY,
    history TEXT,
    updated_at TEXT
);
"""


def init_db() -> None:
    """Cria o schema. Idempotente; chamar no arranque da app."""
    try:
        with _lock, _connect() as conn:
            conn.executescript(_SCHEMA)
        logger.info("Demo-studio storage pronto em %s", _db_path())
    except Exception as e:  # nao deve derrubar a app
        logger.error("Falha a inicializar storage: %s", e)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_session(brief: dict[str, Any], *, research_query: str = "", language: str = "") -> Optional[int]:
    """Guarda um diagnostico gerado. Devolve o id ou None em caso de falha."""
    roi = brief.get("roi_summary") or {}
    row = (
        _now(),
        str(brief.get("business_name") or ""),
        str(brief.get("niche") or ""),
        str(brief.get("niche_label") or ""),
        language or "",
        research_query or "",
        float(roi.get("monthly_gain") or 0),
        float(roi.get("saved_slots_per_month") or 0),
        str(brief.get("executive_summary") or ""),
        json.dumps(brief, ensure_ascii=False),
    )
    try:
        with _lock, _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO demo_session
                    (created_at, business_name, niche, niche_label, language,
                     research_query, monthly_gain, saved_slots, executive_summary, brief_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            return int(cur.lastrowid)
    except Exception as e:
        logger.error("Falha a guardar sessao: %s", e)
        return None


def mark_pushed(session_id: int, notion_page_url: str = "") -> bool:
    """Marca uma sessao como enviada para a Pipeline do Notion."""
    try:
        with _lock, _connect() as conn:
            conn.execute(
                "UPDATE demo_session SET pushed_to_notion = 1, notion_page_url = ? WHERE id = ?",
                (notion_page_url or "", int(session_id)),
            )
        return True
    except Exception as e:
        logger.error("Falha a marcar sessao %s como enviada: %s", session_id, e)
        return False


def list_sessions(limit: int = 50) -> list[dict[str, Any]]:
    """Historico recente de demos (sem o brief_json para ficar leve)."""
    try:
        with _lock, _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, business_name, niche, niche_label, language,
                       monthly_gain, saved_slots, pushed_to_notion, notion_page_url
                FROM demo_session
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error("Falha a listar sessoes: %s", e)
        return []


def set_state(key: str, value: dict[str, Any]) -> bool:
    """Guarda um valor de estado da app (ex: cenario WhatsApp ativo)."""
    try:
        with _lock, _connect() as conn:
            conn.execute(
                """
                INSERT INTO app_state (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, json.dumps(value, ensure_ascii=False), _now()),
            )
        return True
    except Exception as e:
        logger.error("Falha a guardar estado %s: %s", key, e)
        return False


def get_state(key: str) -> Optional[dict[str, Any]]:
    try:
        with _lock, _connect() as conn:
            row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        if row and row["value"]:
            return json.loads(row["value"])
    except Exception as e:
        logger.error("Falha a ler estado %s: %s", key, e)
    return None


def wa_get_history(from_number: str) -> list[dict[str, Any]]:
    """Historico de conversa WhatsApp por remetente (lista role/content)."""
    try:
        with _lock, _connect() as conn:
            row = conn.execute(
                "SELECT history FROM whatsapp_session WHERE from_number = ?", (from_number,)
            ).fetchone()
        if row and row["history"]:
            data = json.loads(row["history"])
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error("Falha a ler historico WhatsApp %s: %s", from_number, e)
    return []


def wa_set_history(from_number: str, history: list[dict[str, Any]]) -> bool:
    try:
        with _lock, _connect() as conn:
            conn.execute(
                """
                INSERT INTO whatsapp_session (from_number, history, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(from_number) DO UPDATE SET history = excluded.history, updated_at = excluded.updated_at
                """,
                (from_number, json.dumps(history, ensure_ascii=False), _now()),
            )
        return True
    except Exception as e:
        logger.error("Falha a guardar historico WhatsApp %s: %s", from_number, e)
        return False


def wa_reset(from_number: str) -> bool:
    try:
        with _lock, _connect() as conn:
            conn.execute("DELETE FROM whatsapp_session WHERE from_number = ?", (from_number,))
        return True
    except Exception as e:
        logger.error("Falha a limpar sessao WhatsApp %s: %s", from_number, e)
        return False


def stats() -> dict[str, Any]:
    """Metricas de venda agregadas para o painel."""
    try:
        with _lock, _connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_demos,
                    COALESCE(SUM(pushed_to_notion), 0) AS pushed,
                    COALESCE(SUM(monthly_gain), 0) AS total_potential_gain,
                    COALESCE(AVG(monthly_gain), 0) AS avg_potential_gain
                FROM demo_session
                """
            ).fetchone()
            by_niche = conn.execute(
                """
                SELECT niche, COUNT(*) AS n
                FROM demo_session
                WHERE niche != ''
                GROUP BY niche
                ORDER BY n DESC
                """
            ).fetchall()
        data = dict(row) if row else {}
        data["by_niche"] = [dict(r) for r in by_niche]
        return data
    except Exception as e:
        logger.error("Falha a calcular stats: %s", e)
        return {"total_demos": 0, "pushed": 0, "total_potential_gain": 0, "avg_potential_gain": 0, "by_niche": []}
