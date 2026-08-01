"""
Sube output/frutinovela_final.mp4 a un bucket de Cloudflare R2.
R2 es compatible con la API de S3, así que usamos boto3 apuntando
a tu endpoint de cuenta en vez de a AWS.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import boto3

OUTPUT_DIR = Path("output")


def main():
    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET"]

    cliente = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

    fecha = datetime.utcnow().strftime("%Y-%m-%d")
    clave_video = f"frutinovelas/{fecha}.mp4"

    cliente.upload_file(
        str(OUTPUT_DIR / "frutinovela_final.mp4"),
        bucket,
        clave_video,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    with open(OUTPUT_DIR / "guion.json", encoding="utf-8") as f:
        guion = json.load(f)

    # Guardamos también la metadata (título/hashtags) junto al video,
    # para que el paso de publicación (o tú manualmente) la use.
    metadata = {
        "video_key": clave_video,
        "titulo": guion["titulo"],
        "hashtags": guion["hashtags"],
    }
    with open(OUTPUT_DIR / "metadata_publicada.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Subido a R2: {clave_video}")


if __name__ == "__main__":
    main()
