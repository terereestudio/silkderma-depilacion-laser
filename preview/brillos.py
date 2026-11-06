"""Genera img/brillos.png: los tres brillos de "Depi Days" como PNG animado (APNG), con fondo transparente.
Uso: python3 preview/brillos.py   (parte de material/brillos-original.png, estrellas amarillas sobre negro)
Cada estrella titila por su cuenta (crece y se aclara), desfasadas entre sí, en bucle.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

RAIZ = Path(__file__).resolve().parent.parent
LADO, CUADROS, MS = 64, 12, 115  # px del archivo (2x de lo que se ve), cuadros, ms por cuadro

a = np.asarray(Image.open(RAIZ / "material" / "brillos-original.png").convert("RGB")).astype(float)
al = np.clip((a.max(2) - 12) / 220, 0, 1)                      # negro -> transparente
rgb = np.clip(a / np.maximum(al[..., None], 1e-3), 0, 255)      # color sin el negro de fondo
lab, n = ndimage.label(al > 0.3)
tam = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
estrellas = np.argsort(tam)[::-1][:3] + 1                        # las 3 estrellas
semilla = np.isin(lab, estrellas) * lab
_, (iy, ix) = ndimage.distance_transform_edt(semilla == 0, return_indices=True)
duena = semilla[iy, ix]                                         # cada píxel de brillo va con su estrella

H, W = al.shape
cuadros = []
for f in range(CUADROS):
    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, e in enumerate(estrellas):
        m = (duena == e) & (al > 0.02)
        ys, xs = np.where(m)
        sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
        p = np.zeros(m[sl].shape + (4,), np.uint8)
        p[..., :3] = rgb[sl]
        p[..., 3] = al[sl] * m[sl] * 255
        im = Image.fromarray(p, "RGBA")
        k = 0.5 - 0.5 * np.cos(2 * np.pi * ((f / CUADROS + i / 3) % 1))   # 0..1, desfasado
        esc = 0.72 + 0.28 * k
        im = im.resize((max(1, round(im.width * esc)), max(1, round(im.height * esc))), Image.LANCZOS)
        q = np.asarray(im).astype(float)
        q[..., 3] *= 0.6 + 0.4 * k
        im = Image.fromarray(q.astype(np.uint8), "RGBA")
        cy, cx = (sl[0].start + sl[0].stop) / 2, (sl[1].start + sl[1].stop) / 2
        lienzo.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))
    cuadros.append(lienzo.resize((LADO, LADO), Image.LANCZOS))

cuadros[0].save(RAIZ / "img" / "brillos.png", save_all=True, append_images=cuadros[1:],
                duration=MS, loop=0, disposal=1, blend=0, optimize=True)
cuadros[0].save(RAIZ / "img" / "brillos-quieto.png", optimize=True)   # para quien prefiere sin movimiento
print("img/brillos.png", (RAIZ / "img" / "brillos.png").stat().st_size // 1024, "KB")
