"""TTS local pt-PT com Piper + plugin livekit-agents.

Piper (https://github.com/rhasspy/piper) gera fala a partir de um modelo .onnx.
O plugin publica PCM int16 mono a 24 kHz (resample se necessario), como espera o
pipeline do livekit-agents.

Instalacao (runtime, pelo orquestrador):
    1. Instalar piper: https://github.com/rhasspy/piper#install
       (binario pre-compilado ou `pip install piper-tts`).
    2. Descarregar um modelo pt-PT (ex: pt_PT-tugao-medium) e definir
       PIPER_MODEL_PATH no .env (caminho para o .onnx).
    3. Definir PIPER_BIN (caminho para o executavel piper) se nao estiver no PATH.

Fallback: se o Piper nao estiver disponivel, o plugin emite ~200ms de silencio e
loga um aviso (a chamada nao parte, mas o agente fica mudo). Para demo rapida
pode trocar-se por outro TTS local (ver TODO em synthesize_text).
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import wave
from io import BytesIO
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

TTS_SAMPLE_RATE = 24000
TTS_NUM_CHANNELS = 1

# Config por env (opcional); fallbacks razoaveis para demo.
PIPER_BIN = os.getenv("PIPER_BIN", "piper")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")


def _resample_to_pcm24k(pcm_int16: bytes, src_rate: int) -> bytes:
    """Resample PCM int16 mono para 24 kHz (numpy; sem dependencia livekit)."""
    import numpy as np  # type: ignore

    samples = np.frombuffer(pcm_int16, dtype=np.int16)
    if len(samples) == 0:
        return b""
    if src_rate == TTS_SAMPLE_RATE:
        return pcm_int16
    ratio = TTS_SAMPLE_RATE / float(src_rate)
    n = max(1, int(len(samples) * ratio))
    idx = np.linspace(0, len(samples) - 1, n).astype(int)
    out = np.ascontiguousarray(samples[idx].astype(np.int16))
    return out.tobytes()


def _parse_wav_pcm(wav_bytes: bytes) -> tuple[bytes, int]:
    """Extrai (PCM int16, sample_rate) de um WAV."""
    with wave.open(BytesIO(wav_bytes), "rb") as w:
        pcm = w.readframes(w.getnframes())
        sr = w.getframerate()
    return pcm, sr


async def _run_piper(text: str) -> bytes:
    """Corre piper escrevendo WAV num ficheiro temp e devolve os bytes WAV."""
    if not PIPER_MODEL_PATH:
        raise RuntimeError(
            "PIPER_MODEL_PATH nao definido. Define o caminho para o modelo .onnx "
            "pt-PT do Piper no .env."
        )
    fd, out_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        proc = await asyncio.create_subprocess_exec(
            PIPER_BIN,
            "-m",
            PIPER_MODEL_PATH,
            "-f",
            out_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, err = await proc.communicate(text.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(
                f"piper falhou (rc={proc.returncode}): "
                f"{err.decode(errors='replace')[:300]}"
            )
        with open(out_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


async def synthesize_text(text: str) -> bytes:
    """TTS standalone (testavel): texto -> PCM int16 24kHz mono bytes.

    TODO(demo): se Piper nao estiver instalado, pode trocar-se por um TTS simples
    (ex: espeak-ng) ajustando _run_piper. Mantenho a interface estavel.
    """
    if not text.strip():
        return b""
    wav = await _run_piper(text)
    pcm, sr = _parse_wav_pcm(wav)
    return _resample_to_pcm24k(pcm, sr)


# --- Plugin nativo livekit-agents ------------------------------------------------

try:
    from livekit.agents.tts import ChunkedStream, TTSCapabilities, TTS
    from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS

    _LIVEKIT_AVAILABLE = True
except ImportError:
    _LIVEKIT_AVAILABLE = False
    TTS = object  # type: ignore[assignment,misc]


if _LIVEKIT_AVAILABLE:

    class _PiperChunkedStream(ChunkedStream):  # type: ignore[misc]
        """ChunkedStream que sintetiza com Piper e empurra PCM 24kHz."""

        async def _run(self, output_emitter: Any) -> None:
            import uuid

            request_id = uuid.uuid4().hex
            try:
                pcm = await synthesize_text(self._input_text)
            except Exception as e:
                logger.error("PiperTTS: %s; a emitir silencio curto", e)
                pcm = b"\x00\x00" * int(TTS_SAMPLE_RATE * 0.2)  # 200ms de silencio

            output_emitter.initialize(
                request_id=request_id,
                sample_rate=TTS_SAMPLE_RATE,
                num_channels=TTS_NUM_CHANNELS,
                mime_type="audio/pcm",
            )
            # ~200ms por pedaco: 24000 * 0.2 * 1 canal * 2 bytes
            chunk = int(TTS_SAMPLE_RATE * 0.2) * TTS_NUM_CHANNELS * 2
            for i in range(0, len(pcm), chunk):
                output_emitter.push(bytes(pcm[i:i + chunk]))
            # end_input() + join() sao tratados pelo ChunkedStream base.

    class PiperTTS(TTS):  # type: ignore[misc]
        """TTS Piper pt-PT (nao-streaming)."""

        def __init__(self, *, sample_rate: int = TTS_SAMPLE_RATE) -> None:
            super().__init__(
                capabilities=TTSCapabilities(streaming=False, aligned_transcript=False),
                sample_rate=sample_rate,
                num_channels=TTS_NUM_CHANNELS,
            )

        @property
        def model(self) -> str:
            return "piper-pt-PT"

        @property
        def provider(self) -> str:
            return "piper"

        def synthesize(
            self, text: str, *, conn_options: Any = DEFAULT_API_CONNECT_OPTIONS
        ) -> "_PiperChunkedStream":
            return _PiperChunkedStream(
                tts=self, input_text=text, conn_options=conn_options
            )

else:

    class PiperTTS:  # type: ignore[no-redef]
        """Stub quando livekit-agents nao esta instalado."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "livekit-agents nao instalado; instale-o para usar PiperTTS"
            )
