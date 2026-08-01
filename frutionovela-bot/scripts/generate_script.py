"""
Genera el guion de un capítulo de "Frutinovela" y lo guarda como JSON.
Salida: output/guion.json
"""
import json
import os
import random
from pathlib import Path

import anthropic

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Personajes disponibles. Cada uno tiene un nombre y una "voz" que se
# asignará luego en tts.py (para que cada fruta suene distinta).
PERSONAJES = [
    "Manzana Roja (dramática, celosa)",
    "Sandía (calmada, sabia, tía del pueblo)",
    "Piña (galán, un poco creído)",
    "Uva Morada (chismosa, mejor amiga)",
    "Limón (villano ácido y rencoroso)",
]

TEMAS = [
    "una boda arruinada por un secreto revelado a último minuto",
    "un triángulo amoroso entre tres frutas del mismo mercado",
    "una herencia que desaparece justo antes de leerse el testamento",
    "un regreso inesperado de alguien que todos creían compostado",
    "una traición descubierta en la fiesta de la cosecha",
]

SYSTEM_PROMPT = """Eres guionista de telenovelas latinoamericanas exageradas,
pero todos los personajes son frutas antropomorfizadas. Tono: dramático,
con música de fondo imaginaria, giros absurdos y un cliffhanger fuerte al
final. Cada capítulo dura entre 30 y 45 segundos hablados.

Responde ÚNICAMENTE con JSON válido, sin texto adicional ni backticks,
con esta forma exacta:

{
  "titulo": "string, máximo 60 caracteres, con gancho para TikTok",
  "hashtags": ["#frutinovela", "#..."],
  "escenas": [
    {
      "personaje": "nombre exacto de la lista de personajes",
      "emocion": "una palabra: furia | llanto | sorpresa | picardia | calma",
      "dialogo": "línea de diálogo, máximo 25 palabras, en español neutro",
      "fondo": "mercado | cocina | jardin | boda | tribunal"
    }
  ]
}

Debe haber entre 6 y 10 escenas."""


def generar_guion() -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    tema = random.choice(TEMAS)
    personajes_txt = "\n".join(f"- {p}" for p in PERSONAJES)

    mensaje = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Personajes disponibles:\n{personajes_txt}\n\n"
                    f"Tema del capítulo de hoy: {tema}.\n"
                    "Usa 3 o 4 personajes de la lista, no todos."
                ),
            }
        ],
    )

    texto = mensaje.content[0].text.strip()
    # Por si el modelo agrega backticks a pesar de la instrucción
    texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    guion = json.loads(texto)
    return guion


if __name__ == "__main__":
    guion = generar_guion()
    with open(OUTPUT_DIR / "guion.json", "w", encoding="utf-8") as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)

    print(f"Guion generado: {guion['titulo']}")
    print(f"{len(guion['escenas'])} escenas")
