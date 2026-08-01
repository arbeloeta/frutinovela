"""
Copia el video final y su metadata a la carpeta videos/ del propio repo.
El commit + push real se hace en el workflow de GitHub Actions (después
de este script), usando git directamente.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")
VIDEOS_DIR = Path("videos")
VIDEOS_DIR.mkdir(exist_ok=True)


def main():
    fecha = datetime.utcnow().strftime("%Y-%m-%d")
    destino_video = VIDEOS_DIR / f"{fecha}.mp4"
    shutil.copy(OUTPUT_DIR / "frutinovela_final.mp4", destino_video)

    with open(OUTPUT_DIR / "guion.json", encoding="utf-8") as f:
        guion = json.load(f)

    metadata = {
        "titulo": guion["titulo"],
        "hashtags": guion["hashtags"],
        "archivo": str(destino_video),
    }

    with open(VIDEOS_DIR / f"{fecha}.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # También la dejamos en output/, que es donde notify.py la espera
    with open(OUTPUT_DIR / "metadata_publicada.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Guardado en el repo: {destino_video}")


if __name__ == "__main__":
    main()
