"""Genera assets/icono.ico a partir del escudo. Solo para la construcción; requiere Pillow."""
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ESCUDO = RAIZ / "assets" / "escudo_colegio.png"
ICONO = RAIZ / "assets" / "icono.ico"
TAMANIOS_ICONO = [(16, 16), (32, 32), (48, 48), (256, 256)]


def main() -> None:
    Image.open(ESCUDO).convert("RGBA").save(ICONO, sizes=TAMANIOS_ICONO)
    print(f"Icono creado en {ICONO}")


if __name__ == "__main__":
    main()
