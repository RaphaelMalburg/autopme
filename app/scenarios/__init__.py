"""Scenario builder module — niche presets and system prompt composition.

Public API:
- build_scenario(niche, business_name, extra=None) -> dict
- list_niches() -> list[dict]
- get_niche_config(niche) -> dict | None
- NICHE_CONFIG, NICHE_ORDER

The FastAPI router is available as `app.scenarios.router.router` and should be mounted
by app/main.py during integration (prefix is already set to /api/scenarios).
"""
from .builder import build_scenario
from .niches import NICHE_CONFIG, NICHE_ORDER, get_niche_config, list_niches

__all__ = [
    "build_scenario",
    "list_niches",
    "get_niche_config",
    "NICHE_CONFIG",
    "NICHE_ORDER",
]
