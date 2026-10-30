"""Genera las imágenes livianas de la página en img/ (WebP, en dos tamaños cada una).
Uso: python3 preview/optimizar_imagenes.py   (después correr python3 preview/build.py)
Las fotos de Flor y del gabinete salen de los originales de material/ (mejor calidad de partida);
las miniaturas de Instagram, de preview/ig/. Los logos y la firma ya están en WebP y se copian.
"""
import shutil
from pathlib import Path
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
MAT, PREV, OUT = RAIZ / "material", RAIZ / "preview", RAIZ / "img"
OUT.mkdir(exist_ok=True)
CALIDAD = 68  # WebP: buen equilibrio entre nitidez y peso para fotos


def abrir(p):
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB")


def recorte_45(im, arriba):
    """Recorta a 4:5 desde `arriba` (sin pasarse del borde)."""
    w, h = im.size
    t = round(w * 5 / 4)
    y = max(0, min(arriba, h - t))
    return im.crop((0, y, w, y + t))


def sin_franja_negra(im):
    """Quita filas casi negras al pie (capturas con barra)."""
    px = im.convert("L").load()
    w, h = im.size
    b = h
    while b > 0 and sum(px[x, b - 1] for x in range(0, w, 8)) / len(range(0, w, 8)) < 20:
        b -= 1
    return im.crop((0, 0, w, b))


def guardar(im, nombre, anchos):
    for a in anchos:
        x = im.resize((a, round(im.height * a / im.width)), Image.LANCZOS)
        x.save(OUT / f"{nombre}-{a}.webp", "WEBP", quality=CALIDAD, method=6)


fotos = {
    # nombre: (original, recorte desde arriba, anchos)
    "flor-hero": (sin_franja_negra(abrir(MAT / "flor-hero-retocada-original.jpg")), 140, (480, 720)),
    "flor-trabajando": (abrir(MAT / "flor-trabajando-original.jpg"), 46, (480, 720)),
    "gabinete": (abrir(MAT / "gabinete-original.jpg"), 60, (480, 720)),
}
for nombre, (im, arriba, anchos) in fotos.items():
    guardar(recorte_45(im, arriba), nombre, anchos)

for f in sorted((PREV / "ig").glob("*.jpg")):
    guardar(abrir(f), "ig-" + f.stem, (320, 480))

for f in ("logo-h.webp", "logo-full-osc.webp", "firma-terereestudio.webp"):
    shutil.copy(PREV / f, OUT / f)

total = sum(p.stat().st_size for p in OUT.glob("*.webp"))
for p in sorted(OUT.glob("*.webp")):
    print(f"{p.name:32} {p.stat().st_size / 1024:6.1f} KB")
print(f"total en img/: {total / 1024:.0f} KB")
