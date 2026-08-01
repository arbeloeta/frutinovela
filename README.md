# Frutinovela Bot

Pipeline 100% automatizado para generar capítulos de "frutinovela" y
tenerlos listos para TikTok, sin ningún servidor propio: todo corre en
GitHub Actions (gratis) + Cloudflare R2 (gratis) + Telegram (gratis).

## Cómo funciona

1. **generate_script.py** — le pide a Claude un guion de 6-10 escenas
   en JSON (personaje, diálogo, emoción, fondo).
2. **tts.py** — convierte cada línea en audio con `edge-tts` (gratis,
   sin API key), con una voz distinta por personaje.
3. **compose_video.py** — arma el video vertical con `ffmpeg`: fondo +
   personaje animado + subtítulos quemados + audio.
4. **upload.py** — sube el resultado a Cloudflare R2.
5. **notify.py** — te manda el video directo a Telegram con el título
   y los hashtags ya escritos, listo para pegar y publicar.

Todo se dispara solo, todos los días, vía `cron` en
`.github/workflows/frutinovela.yml`. También puedes dispararlo a mano
desde la pestaña "Actions" del repo (botón "Run workflow").

## Configuración (una sola vez)

En **Settings → Secrets and variables → Actions** de tu repo, agrega:

| Secret | De dónde sale |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | dashboard de Cloudflare R2 |
| `TELEGRAM_BOT_TOKEN` | @BotFather en Telegram |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot<token>/getUpdates` después de escribirle a tu bot una vez |

## Assets que tienes que poner tú (opcional, mejora mucho el resultado)

Mientras no los subas, el sistema genera rectángulos y fondos de color
sólido como placeholder — funciona, pero se ve genérico.

- `assets/characters/<nombre-personaje-en-slug>.png` — ej.
  `manzana-roja-dramatica-celosa.png` (fondo transparente, ~700px ancho)
- `assets/backgrounds/<fondo>.jpg` — `mercado.jpg`, `cocina.jpg`,
  `jardin.jpg`, `boda.jpg`, `tribunal.jpg` (1080x1920)
- `assets/music/fondo.mp3` — música de fondo en loop, se mezcla al 12%
  de volumen

## Publicación en TikTok

TikTok exige que tu app pase una auditoría antes de poder publicar en
público vía API (si no, los posts quedan en modo privado). Mientras
tramitas eso, `notify.py` te manda el video ya listo por Telegram para
que lo subas tú mismo en segundos. Una vez tengas la app auditada (o
uses un proveedor ya auditado), se reemplaza ese paso por la llamada
real a `/v2/post/publish/video/init/`.

## Costos

$0. Todo corre dentro de las capas gratuitas de GitHub Actions
(minutos ilimitados en repo público), Cloudflare R2 (10GB) y Telegram.
