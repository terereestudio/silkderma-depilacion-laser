"""Pruebas del turnero con respuestas simuladas de NEO Gestión.

Uso: python3 preview/pruebas_turnero.py   (después de python3 preview/build.py)
Necesita Playwright con Chromium. Simula NEO (no lo llama de verdad) y revisa, en celular
(360 y 390 px) y en compu (1366 px), que con cualquier cantidad de días la página no se rompa:
sin errores de JavaScript, sin desplazamiento horizontal, tira de altura fija, chips correctos,
textos sin "undefined" ni "NaN", y que se pueda elegir día y horario.
"""
import asyncio, datetime as dt, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

RAIZ = Path(__file__).resolve().parent.parent
URL = (RAIZ / "index.html").as_uri()
NEO = "https://neo-gestion.vercel.app/api/publico/turnos/silkderma"
HOY = dt.date.today()
GRID = ["09:00", "09:40", "10:20", "11:00", "11:40", "12:20", "13:00", "13:40", "14:20",
        "15:00", "15:40", "16:20", "17:00", "17:40", "18:20", "19:00", "19:40", "20:20"]
SERV = [{"id": 1, "categoria": "Mujeres", "nombre": "Combo 1", "zonas": ["Axilas"], "precio": 23000, "duracion": 40},
        {"id": 2, "categoria": "Hombres", "nombre": "Combo 1", "zonas": ["Pecho"], "precio": None, "duracion": 40}]


def dias(n, desde=None, completos=(), saltear_domingos=False):
    out, d, i = [], desde or HOY + dt.timedelta(days=1), 0
    while len(out) < n:
        if not (saltear_domingos and d.weekday() == 6):
            out.append({"fecha": d.isoformat(), "horarios": GRID, "ocupados": GRID if i in completos else GRID[::4]})
            i += 1
        d += dt.timedelta(days=1)
    return out


def neo(ds, servicios=SERV):
    return {"negocio": "Silkderma", "whatsapp": "5493775445169", "servicios": servicios, "dias": ds}


def mes_unico(n):
    """n días seguidos dentro de un mismo mes futuro (para probar chips de semana)."""
    p = (HOY.replace(day=1) + dt.timedelta(days=40)).replace(day=1)
    return dias(n, desde=p)


raros = dias(12)
raros = list(reversed(raros)) + [raros[3]] + [{"fecha": raros[5]["fecha"], "horarios": [], "ocupados": ["23:59"]}]
sin_horarios = dias(3) + [{"fecha": (HOY + dt.timedelta(days=9)).isoformat(), "horarios": [], "ocupados": []}]

# nombre: (respuesta, días esperados en la tira o None si usa el respaldo, sinDias, completos)
CASOS = {
    "0 días": (neo([]), 0, True, False),
    "1 día": (neo(dias(1)), 1, False, False),
    "2 días": (neo(dias(2)), 2, False, False),
    "7 días": (neo(dias(7)), 7, False, False),
    "12 días un mes": (neo(mes_unico(12)), 12, False, False),
    "mes completo": (neo(mes_unico(28)), 28, False, False),
    "60 días": (neo(dias(60, saltear_domingos=True)), 60, False, False),
    "180 días": (neo(dias(180)), 180, False, False),
    "400 días": (neo(dias(400)), 400, False, False),
    "todos completos": (neo(dias(3, completos=(0, 1, 2))), 3, False, True),
    "desordenados y repetidos": (neo(raros), 12, False, False),
    "día sin horarios": (neo(sin_horarios), 3, False, False),
    "sin servicios": (neo(dias(2), servicios=[]), 2, False, False),
    "datos inválidos": ({"dias": "x"}, None, None, None),
    "NEO 404": (404, None, None, None),
    "NEO caído": ("abort", None, None, None),
    "NEO colgado": ("cuelga", None, None, None),
}

INFO = """() => {
  const t = document.getElementById('dias'), vis = id => !document.getElementById(id).hidden;
  const cards = [...t.querySelectorAll('.dia-dd[data-fecha]')];
  return {
    cards: cards.length,
    altoTira: Math.round(t.getBoundingClientRect().height),
    desbordaPagina: document.scrollingElement.scrollWidth > innerWidth + 1,
    meses: vis('meses') ? document.querySelectorAll('#meses button').length : 0,
    semanas: vis('semanas') ? document.querySelectorAll('#semanas button').length : 0,
    sinDias: vis('sinDias'), completos: vis('completos'),
    textos: document.getElementById('ddEyebrow').textContent + ' | ' + document.getElementById('ddTexto').textContent,
    esqueletos: document.querySelectorAll('.esqueleto').length,
    ordenados: cards.every((c, i) => !i || cards[i - 1].dataset.fecha < c.dataset.fecha),
  };
}"""


async def probar(b, nombre, resp, esperados, sin_dias, completos, w):
    pg = await b.new_page(viewport={"width": w, "height": 900})
    errores, fallas = [], []
    pg.on("pageerror", lambda e: errores.append(str(e)))

    async def handler(route):
        if resp == "abort":
            await route.abort()
        elif resp == "cuelga":
            await asyncio.sleep(7)
            await route.abort()
        elif resp == 404:
            await route.fulfill(status=404, body="{}", content_type="application/json")
        else:
            await route.fulfill(status=200, body=json.dumps(resp), content_type="application/json")

    await pg.route(NEO, handler)
    await pg.goto(URL)
    await pg.wait_for_timeout(5800 if resp == "cuelga" else 900)
    i = await pg.evaluate(INFO)
    if errores: fallas.append("errores JS: " + "; ".join(errores))
    if i["desbordaPagina"]: fallas.append("la página se desplaza a lo ancho")
    if i["esqueletos"]: fallas.append("quedaron tarjetas de carga")
    if "undefined" in i["textos"] or "NaN" in i["textos"]: fallas.append("texto roto: " + i["textos"])
    if not i["ordenados"]: fallas.append("días desordenados o repetidos")
    if esperados is None:  # respaldo: la agenda escrita en el código (puede estar vacía si ya pasó)
        pass
    else:
        if i["cards"] != esperados: fallas.append(f"días en la tira: {i['cards']} (esperados {esperados})")
        if i["sinDias"] != sin_dias: fallas.append("estado 'sin días' incorrecto")
        if i["completos"] != completos: fallas.append("aviso 'todos completos' incorrecto")
    if i["cards"] and i["altoTira"] > 240: fallas.append(f"tira demasiado alta: {i['altoTira']} px")
    # Elegir el último día con turnos libres (el más lejano) y un horario.
    if i["cards"] and not i["completos"]:
        ult = pg.locator("#dias .dia-dd:not(:disabled)").last
        await ult.scroll_into_view_if_needed()
        await ult.click()
        await pg.locator("#slots .chip:not(:disabled)").first.click()
        if await pg.locator("#form").is_hidden(): fallas.append("no aparece el formulario")
        await pg.wait_for_timeout(250)
        j = await pg.evaluate(INFO)
        if j["desbordaPagina"]: fallas.append("se desplaza a lo ancho después de elegir")
    await pg.close()
    detalle = f"{i['cards']} días · chips mes {i['meses']} · semana {i['semanas']}"
    return fallas, detalle, i["textos"]


async def main():
    total = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (360, 390, 1366):
            print(f"\n=== {w} px ===")
            for nombre, (resp, esp, sd, comp) in CASOS.items():
                fallas, detalle, textos = await probar(b, nombre, resp, esp, sd, comp, w)
                total += len(fallas)
                print(("OK   " if not fallas else "FALLA") + f" {nombre:26} {detalle}" + ("" if w != 390 else f"\n      {textos}"))
                for f in fallas: print("      - " + f)
        await b.close()
    print("\nSin fallas." if not total else f"\n{total} fallas.")
    sys.exit(1 if total else 0)


asyncio.run(main())
