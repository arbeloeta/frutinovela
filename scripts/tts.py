"""
Genera un archivo de audio .mp3 por cada escena usando edge-tts
(voces de Microsoft, gratis, sin necesidad de API key).

Asigna una voz distinta a cada personaje para que se distingan al oído.
Salida: output/audio/escena_00.mp3, escena_01.mp3, ...
Además guarda output/duraciones.json con la duración real de cada audio,
que compose_video.py necesita para sincronizar los subtítulos.
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

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
}

# Ajustes de tono/velocidad por emoción, para que no suene siempre plano
ESTILOS_POR_EMOCION = {
    "furia": {"rate": "+15%", "pitch": "+5Hz"},
    "llanto": {"rate": "-10%", "pitch": "-5Hz"},
    "sorpresa": {"rate": "+10%", "pitch": "+10Hz"},
    "picardia": {"rate": "+5%", "pitch": "+3Hz"},
    "calma": {"rate": "-5%", "pitch": "0Hz"},
}


async def generar_audio_escena(texto: str, voz: str, estilo: dict, salida: Path):
    comunicador = edge_tts.Communicate(
        texto, voz, rate=estilo["rate"], pitch=estilo["pitch"]
    )
    await comunicador.save(str(salida))


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
        estilo = ESTILOS_POR_EMOCION.get(escena["emocion"], {"rate": "0%", "pitch": "0Hz"})
        salida = AUDIO_DIR / f"escena_{i:02d}.mp3"

        await generar_audio_escena(escena["dialogo"], voz, estilo, salida)
        duraciones.append(duracion_audio_segundos(salida))
        print(f"Escena {i}: {escena['personaje']} -> {salida.name} ({duraciones[-1]:.2f}s)")

    with open(OUTPUT_DIR / "duraciones.json", "w") as f:
        json.dump(duraciones, f)


if __name__ == "__main__":
    asyncio.run(main())
