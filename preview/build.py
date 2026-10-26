"""Arma la vista previa autocontenida (imágenes embebidas) desde template.html.
Uso: python3 preview/build.py  → escribe preview/silkderma-preview.html e index.html."""
import base64, re
from pathlib import Path

P = Path(__file__).resolve().parent
MIME = {".jpg": "image/jpeg", ".webp": "image/webp", ".png": "image/png"}

def uri(name):
    f = P / name
    return f"data:{MIME[f.suffix]};base64," + base64.b64encode(f.read_bytes()).decode()

html = (P / "template.html").read_text()
fijos = {
    "FLOR": "flor.jpg", "FLOR_M": "flor-mobile.jpg", "FLOR_T": "flor-trabajando.jpg",
    "GABINETE": "gabinete.jpg", "LOGO_H": "logo-h.webp", "LOGO_FULL": "logo-full-osc.webp",
}
for k, v in fijos.items():
    html = html.replace("{{" + k + "}}", uri(v))
html = html.replace("{{FIRMA}}", (P / "firma.txt").read_text().strip())
html = re.sub(r"\{\{IG:([\w-]+)\}\}", lambda m: uri(f"ig/{m.group(1)}.jpg"), html)
assert "{{" not in html, re.findall(r"\{\{[^}]+\}\}", html)
for out in (P / "silkderma-preview.html", P.parent / "index.html"):
    out.write_text(html)
print("ok", len(html) // 1024, "KB")
