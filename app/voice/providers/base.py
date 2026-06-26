"""Interface base do provider de voz (abstracao modular).

Implementacoes (vapi, browser) herdam desta interface. O router e o dashboard
dependem so da interface — trocar de provider nao mexe no resto.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class VoiceProviderError(Exception):
    pass


class VoiceProvider(ABC):
    """Contrato de um provider de voz para a demo."""

    name: str = "base"

    @abstractmethod
    async def status(self) -> dict[str, Any]:
        """Disponibilidade + chaves configuradas + o que falta (para o dashboard)."""
        ...

    @abstractmethod
    async def start_call(
        self,
        *,
        niche: str,
        business_name: str,
        direction: str,
        language: str,
        system_prompt: str,
        first_message: str,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Inicia uma chamada e devolve dados para o dashboard a usar (call_ref, etc.)."""
        ...

    @abstractmethod
    async def end_call(self, call_ref: str) -> dict[str, Any]:
        """Termina uma chamada em curso (best-effort)."""
        ...
