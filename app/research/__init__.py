"""Modulo de pesquisa de prospect na web (AutoPME Demo Studio).

Expoe `research_router` (FastAPI APIRouter prefix /api/research) para integracao
em app/main.py:

    from app.research import research_router
    app.include_router(research_router)

Pesquisa um negocio na web via o plugin `web` do OpenRouter (chave ja existente,
sem novo registo) e devolve dados estruturados + um `extra` pronto a alimentar o
construtor de cenarios (app.scenarios.builder.build_scenario).
"""
from app.research.router import research_router

__all__ = ["research_router"]
