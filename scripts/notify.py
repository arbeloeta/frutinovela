"""
Manda el video final directo a tu chat de Telegram, con el título y los
hashtags ya generados en el caption. Así, si todavía no tienes la API de
TikTok auditada, en 10 segundos lo bajas del chat y lo subes tú mismo
desde el celular.

Requiere:
  - Crear un bot con @BotFather -> te da el TELEGRAM_BOT_TOKEN
  - Escribirle algo a tu bot una vez y sacar tu chat_id con:
    https://api.telegram.org/bot<token>/getUpdates
"""
import json
import os
from pathlib import Path

import requests

OUTPUT_DIR = Path("output")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    with open(OUTPUT_DIR / "metadata_publicada.json", encoding="utf-8") as f:
        meta = json.load(f)

    caption = f"{meta['titulo']}\n\n" + " ".join(meta["hashtags"])
    video_path = OUTPUT_DIR / "frutinovela_final.mp4"

    with open(video_path, "rb") as video_file:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendVideo",
            data={"chat_id": chat_id, "caption": caption[:1024]},
            files={"video": video_file},
            timeout=120,
        )

    if not resp.ok:
        print(f"Telegram respondió {resp.status_code}: {resp.text}")

    resp.raise_for_status()
    print("Enviado a Telegram correctamente.")


if __name__ == "__main__":
    main()
