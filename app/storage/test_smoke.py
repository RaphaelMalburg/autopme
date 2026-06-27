import importlib


def _fresh_db(tmp_path, monkeypatch):
    """Recarrega o modulo db apontando STORAGE_DIR para um tmp isolado."""
    from app.config import settings

    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    from app.storage import db as db_module

    importlib.reload(db_module)
    db_module.init_db()
    return db_module


def _brief(name="Clinica Exemplo", niche="dental", gain=2640.0):
    return {
        "business_name": name,
        "niche": niche,
        "niche_label": "clinica dentaria",
        "executive_summary": "resumo",
        "roi_summary": {"monthly_gain": gain, "saved_slots_per_month": 22.0},
    }


def test_save_list_and_mark_pushed(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)

    sid = db.save_session(_brief(), research_query="dentista porto", language="pt-PT")
    assert isinstance(sid, int)

    sessions = db.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["business_name"] == "Clinica Exemplo"
    assert sessions[0]["pushed_to_notion"] == 0
    # brief_json nao deve vir na listagem (mantida leve)
    assert "brief_json" not in sessions[0]

    assert db.mark_pushed(sid, "https://notion.so/page") is True
    sessions = db.list_sessions()
    assert sessions[0]["pushed_to_notion"] == 1
    assert sessions[0]["notion_page_url"] == "https://notion.so/page"


def test_stats_aggregates(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    db.save_session(_brief(niche="dental", gain=1000))
    db.save_session(_brief(niche="dental", gain=3000))
    sid = db.save_session(_brief(niche="legal", gain=2000))
    db.mark_pushed(sid)

    s = db.stats()
    assert s["total_demos"] == 3
    assert s["pushed"] == 1
    assert s["total_potential_gain"] == 6000
    assert s["avg_potential_gain"] == 2000
    niches = {row["niche"]: row["n"] for row in s["by_niche"]}
    assert niches == {"dental": 2, "legal": 1}
