"""
Genera un archivo de audio .mp3 por cada escena.

Motor principal: edge-tts (voces de Microsoft, gratis, sin API key,
buena variedad de voces por personaje). Como es un servicio no oficial
que de vez en cuando devuelve 403/503 por unas horas, este script:
  1. Reintenta con backoff si falla momentáneamente.
  2. Si sigue fallando tras varios intentos, cae a gTTS (motor de
     Google Translate, distinto servicio, gratis, sin key) para que
     el capítulo se genere igual, aunque con una sola voz genérica.

Salida: output/audio/escena_00.mp3, escena_01.mp3, ...
Además guarda output/duraciones.json con la duración real de cada audio,
que compose_video.py necesita para sincronizar los subtítulos.
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts
from gtts import gTTS

OUTPUT_DIR = Path("output")
AUDIO_DIR = OUTPUT_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Mapeo de personaje -> voz de edge-tts. Puedes escuchar el catálogo
# completo con: edge-tts --list-voices
VOCES = {
    "Manzana Roja (dramática, celosa)": "es-MX-DaliaNeural",
    "Sandía (calmada, sabia, tía del pueblo)": "es-CO-SalomeNeural",
    "Piña (galán, un poco creído)": "es-MX-JorgeNeural",
    "Uva Morada (chismosa, mejor amiga)": "es-AR-ElenaNeural",
    "Limón (villano ácido y rencoroso)": "es-ES-AlvaroNeural",
    "Coco (padre estricto, dueño del mercado)": "es-VE-SebastianNeural",
    "Frambuesa (ingenua, enamorada en secreto)": "es-PE-CamilaNeural",
}

# Ajustes de tono/velocidad por emoción, para que no suene siempre plano.
# IMPORTANTE: edge-tts exige el signo explícito (+ o -), incluso en 0.
ESTILOS_POR_EMOCION = {
    "furia": {"rate": "+15%", "pitch": "+5Hz"},
    "llanto": {"rate": "-10%", "pitch": "-5Hz"},
    "sorpresa": {"rate": "+10%", "pitch": "+10Hz"},
    "picardia": {"rate": "+5%", "pitch": "+3Hz"},
    "calma": {"rate": "-5%", "pitch": "+0Hz"},
}
ESTILO_POR_DEFECTO = {"rate": "+0%", "pitch": "+0Hz"}

# Reintentos ante fallos momentáneos del servicio de edge-tts
MAX_INTENTOS = 4
ESPERA_BASE_SEGUNDOS = 3  # se duplica en cada intento: 3s, 6s, 12s...


async def _intentar_con_edge_tts(texto: str, voz: str, estilo: dict, salida: Path) -> bool:
    """Devuelve True si logró generar el audio, False si hay que caer a gTTS."""
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            comunicador = edge_tts.Communicate(
                text=texto,
                voice=voz,
                rate=estilo["rate"],
                pitch=estilo["pitch"],
                volume="+0%",
            )
            await comunicador.save(str(salida))
            return True
        except Exception as error:
            espera = ESPERA_BASE_SEGUNDOS * (2 ** (intento - 1))
            print(
                f"  edge-tts falló (intento {intento}/{MAX_INTENTOS}): {error}"
                + (f" -> reintentando en {espera}s" if intento < MAX_INTENTOS else "")
            )
            if intento < MAX_INTENTOS:
                await asyncio.sleep(espera)
    return False


def _generar_con_gtts(texto: str, salida: Path):
    """Plan B: motor distinto (Google Translate), sin variedad de voces
    por personaje, pero mantiene el pipeline funcionando."""
    try:
        tts = gTTS(text=texto, lang="es")
        tts.save(str(salida))
    except Exception as error:
        raise RuntimeError(
            "Fallaron edge-tts Y gTTS en la misma ejecución. "
            "Probablemente ambos servicios están caídos a la vez "
            "(raro) o hay un problema de red en el runner. "
            f"Error original de gTTS: {error}"
        ) from error


async def generar_audio_escena(texto: str, voz: str, estilo: dict, salida: Path):
    exito = await _intentar_con_edge_tts(texto, voz, estilo, salida)
    if not exito:
        print("  edge-tts no respondió tras varios intentos, usando gTTS como respaldo")
        _generar_con_gtts(texto, salida)


def duracion_audio_segundos(path: Path) -> float:
    resultado = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(resultado.stdout.strip())


async def main():
    with open(OUTPUT_DIR / "guion.json", encoding="utf-8") as f:
        guion = json.load(f)

    duraciones = []

    for i, escena in enumerate(guion["escenas"]):
        voz = VOCES.get(escena["personaje"], "es-MX-DaliaNeural")
        estilo = ESTILOS_POR_EMOCION.get(escena["emocion"], ESTILO_POR_DEFECTO)
        salida = AUDIO_DIR / f"escena_{i:02d}.mp3"

        await generar_audio_escena(escena["dialogo"], voz, estilo, salida)
        duraciones.append(duracion_audio_segundos(salida))
        print(f"Escena {i}: {escena['personaje']} -> {salida.name} ({duraciones[-1]:.2f}s)")

    with open(OUTPUT_DIR / "duraciones.json", "w") as f:
        json.dump(duraciones, f)


if __name__ == "__main__":
    asyncio.run(main())
