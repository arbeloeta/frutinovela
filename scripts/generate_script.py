"""
Genera el guion de un capítulo de "Frutinovela" usando Gemini (gratis,
sin tarjeta) y lo guarda como JSON.
Salida: output/guion.json
"""
import json
import os
import random
from pathlib import Path

from google import genai
from google.genai import types

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# NOTA: Gemini 2.5 Flash está en el tier gratis (10 req/min, 250 req/día
# al momento de escribir esto). Google anunció que se retira el 16 de
# octubre de 2026 -> si esta fecha ya pasó, cambia el string de abajo
# por el modelo Flash gratuito vigente (revisa ai.google.dev/pricing).
MODELO = "gemini-2.5-flash-lite"

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
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    tema = random.choice(TEMAS)
    personajes_txt = "\n".join(f"- {p}" for p in PERSONAJES)

    prompt = (
        f"Personajes disponibles:\n{personajes_txt}\n\n"
        f"Tema del capítulo de hoy: {tema}.\n"
        "Usa 3 o 4 personajes de la lista, no todos."
    )

    respuesta = cliente.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            max_output_tokens=1500,
        ),
    )

    texto = respuesta.text.strip()
    texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    guion = json.loads(texto)
    return guion


if __name__ == "__main__":
    guion = generar_guion()
    with open(OUTPUT_DIR / "guion.json", "w", encoding="utf-8") as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)

    print(f"Guion generado: {guion['titulo']}")
    print(f"{len(guion['escenas'])} escenas")
