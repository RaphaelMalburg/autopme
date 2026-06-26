"""Smoke test: minta um AccessToken JWT (devkey/secret) para uma room de teste
e imprime-o. Valida que o livekit-api + as credenciais (LIVEKIT_API_KEY/SECRET)
funcionam contra o servidor local.

Correr (precisa de livekit-api instalado e .env com as chaves):
    python -m app.voice.smoke_token
    python -m app.voice.smoke_token --room demo-test --identity tester

Se livekit-api nao estiver instalado, falha com ImportError — instalar:
    pip install livekit-api
"""
from __future__ import annotations

import argparse
import asyncio

from app.config import settings


async def mint_token(room: str, identity: str) -> str:
    from livekit import api

    return (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_publish_data=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Minta um token LiveKit de teste.")
    parser.add_argument("--room", default="demo-smoke-test")
    parser.add_argument("--identity", default="smoke-tester")
    args = parser.parse_args()

    token = await mint_token(args.room, args.identity)
    print("room:", args.room)
    print("ws_url:", settings.livekit_url)
    print("api_key:", settings.livekit_api_key)
    print("token:", token)


if __name__ == "__main__":
    asyncio.run(main())
