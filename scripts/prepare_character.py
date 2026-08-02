"""
Convierte una FOTO REAL de una fruta en el PNG de personaje que espera
compose_video.py: le quita el fondo automáticamente y le dibuja una
cara encima (ojos, cejas, boca) según la personalidad del personaje.

Uso:
    python scripts/prepare_character.py <foto.jpg> "<nombre exacto del personaje>"

Ejemplo:
    python scripts/prepare_character.py mis_fotos/manzana.jpg \
        "Manzana Roja (dramática, celosa)"

Consejo para la foto: fotografía la fruta sobre un fondo simple y
parejo (una hoja de papel blanco funciona perfecto) y con buena luz.
Cuanto más contraste haya entre la fruta y el fondo, mejor la recorta
la IA de quitado de fondo.
"""
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw
from rembg import remove

CHARACTERS_DIR = Path("assets/characters")
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
TAMANO_FINAL = 700

# Configuración de cara por personaje: posición/estilo de ojos, cejas y
# boca, en fracciones (0-1) relativas al recuadro de la fruta ya
# recortada. Ajusta estos números si en tu foto la cara queda mal
# ubicada (por ejemplo si la fruta es muy alargada).
CONFIG_CARA = {
    "manzana-roja-dramatica-celosa": {
        "ojos_y": 0.42, "ojos_x": (0.36, 0.64), "ojo_ancho": 0.05,
        "cejas": "fruncidas", "boca": "puchero", "color_rasgos": "#2B0A0A",
    },
    "sandia-calmada-sabia-tia-del-pueblo": {
        "ojos_y": 0.48, "ojos_x": (0.38, 0.62), "ojo_ancho": 0.045,
        "cejas": "relajadas", "boca": "sonrisa_suave", "color_rasgos": "#2B1A0D",
    },
    "pina-galan-un-poco-creido": {
        "ojos_y": 0.45, "ojos_x": (0.37, 0.63), "ojo_ancho": 0.05,
        "cejas": "arqueada_una", "boca": "sonrisa_lado", "color_rasgos": "#1A1A1A",
    },
    "uva-morada-chismosa-mejor-amiga": {
        "ojos_y": 0.44, "ojos_x": (0.36, 0.64), "ojo_ancho": 0.065,
        "cejas": "levantadas", "boca": "o_chisme", "color_rasgos": "#2B0A2B",
    },
    "limon-villano-acido-y-rencoroso": {
        "ojos_y": 0.46, "ojos_x": (0.37, 0.63), "ojo_ancho": 0.045,
        "cejas": "villano", "boca": "malvada", "color_rasgos": "#3A3A0A",
    },
    "coco-padre-estricto-dueno-del-mercado": {
        "ojos_y": 0.44, "ojos_x": (0.37, 0.63), "ojo_ancho": 0.045,
        "cejas": "seria_una_linea", "boca": "bigote_serio", "color_rasgos": "#1A1A1A",
    },
    "frambuesa-ingenua-enamorada-en-secreto": {
        "ojos_y": 0.42, "ojos_x": (0.36, 0.64), "ojo_ancho": 0.06,
        "cejas": "ninguna", "boca": "sonrisa_timida", "color_rasgos": "#8E123F",
    },
}


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
    return re.sub(r"[\s_]+", "-", texto)


def quitar_fondo_y_encuadrar(ruta_foto: Path) -> Image.Image:
    original = Image.open(ruta_foto).convert("RGBA")
    sin_fondo = remove(original)

    caja = sin_fondo.getbbox()
    if caja is None:
        raise ValueError(
            "No se detectó ningún objeto en la foto tras quitar el fondo. "
            "Prueba con más contraste entre la fruta y el fondo."
        )
    recortado = sin_fondo.crop(caja)

    lado = max(recortado.width, recortado.height)
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lienzo.paste(
        recortado,
        ((lado - recortado.width) // 2, (lado - recortado.height) // 2),
        recortado,
    )
    return lienzo.resize((TAMANO_FINAL, TAMANO_FINAL), Image.LANCZOS)


def dibujar_cara(imagen: Image.Image, config: dict) -> Image.Image:
    dibujo = ImageDraw.Draw(imagen)
    lado = imagen.width
    color = config["color_rasgos"]
    ojo_y = int(config["ojos_y"] * lado)
    ojo_r = int(config["ojo_ancho"] * lado)
    x_izq = int(config["ojos_x"][0] * lado)
    x_der = int(config["ojos_x"][1] * lado)

    # --- ojos base (blanco + pupila) ---
    for x in (x_izq, x_der):
        dibujo.ellipse([x - ojo_r, ojo_y - ojo_r, x + ojo_r, ojo_y + ojo_r], fill="white")
        pr = int(ojo_r * 0.5)
        dibujo.ellipse([x - pr, ojo_y - pr, x + pr, ojo_y + pr], fill=color)

    # --- cejas según personalidad ---
    ceja_y = ojo_y - ojo_r - int(0.02 * lado)
    grosor = max(4, int(0.012 * lado))
    estilo_cejas = config["cejas"]
    if estilo_cejas == "fruncidas":
        dibujo.line([x_izq - ojo_r, ceja_y + 10, x_izq + ojo_r, ceja_y - 10], fill=color, width=grosor)
        dibujo.line([x_der - ojo_r, ceja_y - 10, x_der + ojo_r, ceja_y + 10], fill=color, width=grosor)
    elif estilo_cejas == "levantadas":
        for x in (x_izq, x_der):
            dibujo.arc([x - ojo_r, ceja_y - 15, x + ojo_r, ceja_y + 15], 200, 340, fill=color, width=grosor)
    elif estilo_cejas == "arqueada_una":
        dibujo.arc([x_der - ojo_r, ceja_y - 20, x_der + ojo_r, ceja_y + 10], 200, 340, fill=color, width=grosor)
        dibujo.line([x_izq - ojo_r, ceja_y, x_izq + ojo_r, ceja_y], fill=color, width=grosor)
    elif estilo_cejas == "villano":
        dibujo.line([x_izq - ojo_r, ceja_y + 10, x_izq + ojo_r, ceja_y - 15], fill=color, width=grosor)
        dibujo.line([x_der - ojo_r, ceja_y - 15, x_der + ojo_r, ceja_y + 10], fill=color, width=grosor)
    elif estilo_cejas == "seria_una_linea":
        dibujo.line([x_izq - ojo_r, ceja_y, x_der + ojo_r, ceja_y], fill=color, width=grosor)
    # "relajadas" y "ninguna" -> no se dibuja nada extra

    # --- boca según personalidad ---
    boca_y = int(0.66 * lado)
    cx = lado // 2
    ancho_boca = int(0.16 * lado)
    estilo_boca = config["boca"]
    if estilo_boca == "puchero":
        dibujo.arc([cx - ancho_boca, boca_y - 15, cx + ancho_boca, boca_y + 25], 200, 340, fill=color, width=grosor)
    elif estilo_boca == "sonrisa_suave":
        dibujo.arc([cx - ancho_boca, boca_y - 20, cx + ancho_boca, boca_y + 20], 20, 160, fill=color, width=grosor)
    elif estilo_boca == "sonrisa_lado":
        dibujo.arc([cx - ancho_boca, boca_y - 10, cx + int(ancho_boca * 1.3), boca_y + 25], 10, 140, fill=color, width=grosor)
    elif estilo_boca == "o_chisme":
        r = int(ancho_boca * 0.35)
        dibujo.ellipse([cx - r, boca_y - r, cx + r, boca_y + r], fill=color)
    elif estilo_boca == "malvada":
        dibujo.polygon(
            [(cx - ancho_boca, boca_y), (cx + ancho_boca, boca_y - 15), (cx, boca_y + 35)],
            fill=color,
        )
    elif estilo_boca == "bigote_serio":
        dibujo.line([cx - ancho_boca, boca_y, cx + ancho_boca, boca_y], fill=color, width=grosor + 4)
    elif estilo_boca == "sonrisa_timida":
        dibujo.arc([cx - int(ancho_boca * 0.6), boca_y - 10, cx + int(ancho_boca * 0.6), boca_y + 15], 20, 160, fill=color, width=max(3, grosor - 2))

    return imagen


def main():
    if len(sys.argv) != 3:
        print('Uso: python scripts/prepare_character.py <foto.jpg> "<nombre del personaje>"')
        sys.exit(1)

    ruta_foto = Path(sys.argv[1])
    nombre_personaje = sys.argv[2]
    clave = slug(nombre_personaje)

    if clave not in CONFIG_CARA:
        print(f"Aviso: no hay configuración de cara para '{clave}'.")
        print("Personajes conocidos:", ", ".join(CONFIG_CARA.keys()))
        sys.exit(1)

    imagen = quitar_fondo_y_encuadrar(ruta_foto)
    imagen = dibujar_cara(imagen, CONFIG_CARA[clave])

    salida = CHARACTERS_DIR / f"{clave}.png"
    imagen.save(salida)
    print(f"Personaje listo: {salida}")


if __name__ == "__main__":
    main()
