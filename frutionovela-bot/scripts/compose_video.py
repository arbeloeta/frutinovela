"""
Arma el video vertical (1080x1920, formato TikTok) a partir de:
  - output/guion.json          (texto y metadata de cada escena)
  - output/audio/escena_NN.mp3 (voz generada por tts.py)
  - assets/backgrounds/<fondo>.jpg   (si no existe, genera un color sólido)
  - assets/characters/<personaje>.png (si no existe, genera un rectángulo de color)
  - assets/music/fondo.mp3     (opcional, música de fondo en loop)

Salida final: output/frutinovela_final.mp4
"""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

OUTPUT_DIR = Path("output")
CLIPS_DIR = OUTPUT_DIR / "clips"
CLIPS_DIR.mkdir(exist_ok=True)
AUDIO_DIR = OUTPUT_DIR / "audio"

ASSETS = Path("assets")
BACKGROUNDS = ASSETS / "backgrounds"
CHARACTERS = ASSETS / "characters"
MUSIC = ASSETS / "music" / "fondo.mp3"

ANCHO, ALTO = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Un color de respaldo por tipo de fondo, por si aún no subiste el asset real
COLOR_FONDO = {
    "mercado": "0xE8B84B",
    "cocina": "0xD98E5A",
    "jardin": "0x7FBF6B",
    "boda": "0xF2D7EE",
    "tribunal": "0x8C8C8C",
}
# Un color por personaje, mismo criterio
COLOR_PERSONAJE = {
    "Manzana Roja (dramática, celosa)": "0xD9312B",
    "Sandía (calmada, sabia, tía del pueblo)": "0x2E8B57",
    "Piña (galán, un poco creído)": "0xE8C34A",
    "Uva Morada (chismosa, mejor amiga)": "0x7B4B94",
    "Limón (villano ácido y rencoroso)": "0xE8E13B",
}


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
    return re.sub(r"[\s_]+", "-", texto)


def escapar_drawtext(texto: str) -> str:
    # ffmpeg drawtext necesita escapar : ' , y saltos de línea
    texto = texto.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")
    return texto


def obtener_fondo(nombre_fondo: str, duracion: float) -> Path:
    ruta = BACKGROUNDS / f"{nombre_fondo}.jpg"
    if ruta.exists():
        return ruta

    # No hay asset real todavía: generamos un color sólido como placeholder
    color = COLOR_FONDO.get(nombre_fondo, "0x336699")
    salida = CLIPS_DIR / f"bg_{nombre_fondo}.jpg"
    if not salida.exists():
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c={color}:s={ANCHO}x{ALTO}",
                "-frames:v", "1", str(salida),
            ],
            check=True, capture_output=True,
        )
    return salida


def obtener_personaje(nombre_personaje: str) -> Path:
    ruta = CHARACTERS / f"{slug(nombre_personaje)}.png"
    if ruta.exists():
        return ruta

    color = COLOR_PERSONAJE.get(nombre_personaje, "0xCCCCCC")
    salida = CLIPS_DIR / f"char_{slug(nombre_personaje)}.png"
    if not salida.exists():
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c={color}:s=700x700",
                "-frames:v", "1", str(salida),
            ],
            check=True, capture_output=True,
        )
    return salida


def renderizar_escena(i: int, escena: dict, duracion: float) -> Path:
    fondo = obtener_fondo(escena["fondo"], duracion)
    personaje = obtener_personaje(escena["personaje"])
    audio = AUDIO_DIR / f"escena_{i:02d}.mp3"
    texto = escapar_drawtext(escena["dialogo"])
    salida = CLIPS_DIR / f"escena_{i:02d}.mp4"

    filtro = (
        f"[0:v]scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
        f"crop={ANCHO}:{ALTO}[bg];"
        f"[1:v]scale=700:-1[char];"
        f"[bg][char]overlay=x=(W-w)/2:y=H-h-260+15*sin(2*PI*t*1.2)[v1];"
        f"[v1]drawtext=fontfile={FONT}:text='{texto}':fontsize=52:"
        f"fontcolor=white:borderw=3:bordercolor=black:"
        f"box=1:boxcolor=black@0.45:boxborderw=14:"
        f"x=(w-text_w)/2:y=h-330:line_spacing=8[vout]"
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duracion), "-i", str(fondo),
            "-loop", "1", "-t", str(duracion), "-i", str(personaje),
            "-i", str(audio),
            "-filter_complex", filtro,
            "-map", "[vout]", "-map", "2:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            str(salida),
        ],
        check=True, capture_output=True,
    )
    return salida


def concatenar_escenas(clips: list[Path]) -> Path:
    lista_path = CLIPS_DIR / "lista.txt"
    with open(lista_path, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    sin_musica = OUTPUT_DIR / "sin_musica.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(lista_path), "-c", "copy", str(sin_musica),
        ],
        check=True, capture_output=True,
    )
    return sin_musica


def mezclar_musica(video_sin_musica: Path) -> Path:
    final = OUTPUT_DIR / "frutinovela_final.mp4"

    if not MUSIC.exists():
        # Sin música de fondo disponible todavía: el video queda solo con las voces
        video_sin_musica.rename(final)
        return final

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_sin_musica),
            "-stream_loop", "-1", "-i", str(MUSIC),
            "-filter_complex",
            "[1:a]volume=0.12[musica];[0:a][musica]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-shortest",
            str(final),
        ],
        check=True, capture_output=True,
    )
    return final


def main():
    with open(OUTPUT_DIR / "guion.json", encoding="utf-8") as f:
        guion = json.load(f)
    with open(OUTPUT_DIR / "duraciones.json") as f:
        duraciones = json.load(f)

    clips = [
        renderizar_escena(i, escena, duraciones[i] + 0.4)
        for i, escena in enumerate(guion["escenas"])
    ]

    sin_musica = concatenar_escenas(clips)
    final = mezclar_musica(sin_musica)
    print(f"Video final listo: {final}")


if __name__ == "__main__":
    main()
