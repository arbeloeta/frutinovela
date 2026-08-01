"""
Genera el guion de un capítulo de "Frutinovela" usando Gemini.
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

MODELO = "gemini-3.5-flash"

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

SYSTEM_PROMPT = """
Eres un guionista profesional de TikTok.

Debes responder EXCLUSIVAMENTE con JSON válido.

Formato:

{
  "titulo": "texto",
  "hashtags": [
    "#frutinovela",
    "#telenovela"
  ],
  "escenas": [
    {
      "personaje": "nombre exacto",
      "emocion": "furia",
      "dialogo": "texto",
      "fondo": "mercado"
    }
  ]
}

No escribas absolutamente nada fuera del JSON.
"""


def generar_guion():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception("No existe GEMINI_API_KEY")

    cliente = genai.Client(api_key=api_key)

    tema = random.choice(TEMAS)

    personajes = "\n".join(f"- {p}" for p in PERSONAJES)

    prompt = f"""
Personajes disponibles:

{personajes}

Tema:

{tema}

Usa únicamente 3 o 4 personajes.

Entre 6 y 10 escenas.

El JSON debe ser PERFECTAMENTE válido.
"""

    respuesta = cliente.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=1,
            max_output_tokens=800,
        ),
    )

    texto = respuesta.text or ""

    texto = (
        texto.replace("```json", "")
        .replace("```", "")
        .strip()
    )

    print("\n===== RESPUESTA GEMINI =====\n")
    print(texto)
    print("\n============================\n")

    if not texto:
        raise Exception("Gemini devolvió una respuesta vacía.")

    try:
        return json.loads(texto)

    except Exception as e:

        with open(
            OUTPUT_DIR / "respuesta_gemini.txt",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(texto)

        raise Exception(
            f"JSON inválido.\nSe ha guardado la respuesta en output/respuesta_gemini.txt\n\n{e}"
        )


if __name__ == "__main__":

    guion = generar_guion()

    with open(
        OUTPUT_DIR / "guion.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            guion,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Guion generado: {guion['titulo']}")
    print(f"Escenas: {len(guion['escenas'])}")
