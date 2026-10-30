"""Arma la página desde template.html.
Uso: python3 preview/build.py  → escribe index.html (raíz) y preview/silkderma-preview.html.
Las imágenes son archivos WebP en img/ (se generan con preview/optimizar_imagenes.py) y se
enlazan, no se incrustan: así el navegador baja solo las que necesita y cuando las necesita.
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent
RAIZ = P.parent
html = (P / "template.html").read_text()

usadas = set(re.findall(r"\{\{IMG\}\}([\w.-]+\.webp)", html))
faltan = [n for n in usadas if not (RAIZ / "img" / n).exists()]
assert not faltan, f"faltan imágenes en img/ (correr optimizar_imagenes.py): {faltan}"

for destino, prefijo in ((RAIZ / "index.html", "img/"), (P / "silkderma-preview.html", "../img/")):
    salida = html.replace("{{IMG}}", prefijo)
    assert "{{" not in salida, re.findall(r"\{\{[^}]+\}\}", salida)
    destino.write_text(salida)
print("ok", len(html.encode()) // 1024, "KB de HTML,", len(usadas), "imágenes enlazadas")
