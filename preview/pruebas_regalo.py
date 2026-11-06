"""Pruebas del canje de regalos (?regalo=) con NEO simulado, en celular (390 px) y compu.
Uso: python3 preview/build.py && python3 preview/pruebas_regalo.py [carpeta-para-capturas]
Revisa: que nunca aparezcan precios ni montos, el canje por combo y por monto (varios turnos),
código inexistente, ya canjeado, vencido, anulado, demasiados intentos, horario tomado (409)
y consentimiento sin tildar.
"""
import asyncio, json, re, sys
from pathlib import Path
from playwright.async_api import async_playwright

RAIZ = Path(__file__).resolve().parent.parent
URL = (RAIZ / "index.html").as_uri()
CAPT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
API = "https://neo-gestion.vercel.app/api/publico/"
GRID = ["09:00", "09:40", "10:20", "11:00", "11:40", "12:20"]
AGENDA = {"negocio": "Silkderma", "whatsapp": "5493775445169",
          "servicios": [{"id": "s2", "categoria": "Mujeres", "nombre": "Combo 2", "zonas": ["Axilas"], "precio": 29000.0, "duracion": 40}],
          "dias": [{"fecha": f"2026-12-{d:02d}", "horarios": GRID, "ocupados": ["09:00"]} for d in (10, 11, 12)]}
S = {i: {"id": f"s{i}", "nombre": f"Combo {i}", "zonas": ["Axilas", "Cavado completo"]} for i in range(1, 5)}
COMBO = {"numero": "0123", "tipo": "combo", "para": "María", "de": "Juan", "mensaje": "¡Feliz cumple!", "vence": "2026-12-31",
         "servicio": S[2], "servicios_disponibles": None}


def monto(elegidos):
    # Simula el saldo en NEO: entra hasta 3 combos en total.
    disp = [] if len(elegidos) >= 3 else [S[1], S[2], S[3]] if len(elegidos) < 2 else [S[1]]
    return {"numero": "0456", "tipo": "monto", "para": None, "de": "Las chicas del trabajo", "mensaje": None, "vence": "2026-12-31",
            "servicio": None, "servicios_disponibles": disp}


PRECIO = re.compile(r"\$\s?\d|\d{2}\.\d{3}|saldo|monto", re.I)


async def caso(b, nombre, codigo, get, post=None, pasos=None, w=390):
    pg = await b.new_page(viewport={"width": w, "height": 844}, device_scale_factor=2 if w < 800 else 1)
    errores, posts, fallas = [], [], []
    pg.on("pageerror", lambda e: errores.append(str(e)))

    async def h(route, req):
        url = req.url
        if "/vouchers/" in url and req.method == "POST":
            posts.append(json.loads(req.post_data))
            st, body = post(len(posts)) if post else (200, {})
            return await route.fulfill(status=st, body=json.dumps(body), content_type="application/json")
        if "/vouchers/" in url:
            m = re.search(r"elegidos=([^&]+)", url)
            el = m.group(1).split("%2C") if m else []
            el = [x for x in ",".join(el).split(",") if x]
            st, body = get(el)
            return await route.fulfill(status=st, body=json.dumps(body), content_type="application/json")
        if "/turnos/" in url:
            return await route.fulfill(status=200, body=json.dumps(AGENDA), content_type="application/json")
        await route.abort()

    await pg.route(API + "**", h)
    await pg.goto(URL + "?regalo=" + codigo)
    await pg.wait_for_selector("#regaloPantalla > *:not(.r-cargando)", timeout=8000)
    if pasos:
        await pasos(pg, fallas)
    texto = await pg.locator("#regalo").inner_text()
    if PRECIO.search(texto): fallas.append("se ve un precio o monto: " + PRECIO.search(texto).group(0))
    if errores: fallas.append("errores JS: " + "; ".join(errores))
    if await pg.evaluate("document.scrollingElement.scrollWidth > innerWidth + 1"): fallas.append("desborda a lo ancho")
    if CAPT: await pg.locator(".regalo-hoja").screenshot(path=str(CAPT / f"regalo-{nombre}.png"))
    await pg.close()
    print(("OK   " if not fallas else "FALLA") + f" {nombre}" + "".join("\n      - " + f for f in fallas))
    return fallas, posts


async def elegir_turno(pg, i=0, dia=0, hora=0):
    t = pg.locator(".r-turno").nth(i)
    await t.locator(".r-dia").nth(dia).click()
    t = pg.locator(".r-turno").nth(i)
    await t.locator(".r-horas .chip:not(:disabled)").nth(hora).click()


async def datos(pg, tildar=True):
    await pg.click("#regalo button:text-is(\"Seguir\")")
    await pg.fill("#regalo input[name=nombre]", "María G.")
    await pg.fill("#regalo input[name=telefono]", "3775 123456")
    if tildar: await pg.check("#regalo input[name=ok]")
    await pg.click("#rEnviar")
    await pg.wait_for_timeout(400)


async def main():
    total = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()

        async def p_combo(pg, f):
            if "María, ¡te regalaron" not in await pg.locator("#regalo").inner_text(): f.append("falta el saludo con el nombre")
            if CAPT: await pg.locator(".regalo-hoja").screenshot(path=str(CAPT / "regalo-combo-bienvenida.png"))
            await pg.click("#regalo >> text=Elegir día y horario")
            await elegir_turno(pg)
            if CAPT: await pg.locator(".regalo-hoja").screenshot(path=str(CAPT / "regalo-combo-horario.png"))
            await datos(pg)
            await pg.wait_for_timeout(1500)
            if "Ya reservamos tu turno" not in await pg.locator("#regalo").inner_text(): f.append("no llegó a la pantalla de éxito")
        fl, posts = await caso(b, "combo-exito", "k7p29xqm", lambda e: (200, COMBO),
                               lambda n: (200, {"numero": "0123", "turnos": [{"servicio": "Combo 2", "fecha": "2026-12-10", "hora": "09:40"}]}), p_combo)
        total += len(fl)
        if posts and not (posts[0].get("servicio_id") == "s2" and posts[0].get("consentimiento") is True and posts[0]["fecha"] == "2026-12-10"):
            print("FALLA cuerpo del canje por combo:", posts[0]); total += 1

        async def p_monto(pg, f):
            for _ in range(3):
                await pg.locator(".r-op .btn").first.click(); await pg.wait_for_timeout(300)
            if await pg.locator(".r-op").count(): f.append("sigue ofreciendo combos cuando ya no entran")
            if CAPT: await pg.locator(".regalo-hoja").screenshot(path=str(CAPT / "regalo-monto-combos.png"))
            await pg.click("#regalo >> text=Elegir días y horarios")
            for i in range(3): await elegir_turno(pg, i, dia=0, hora=0)   # mismo día: el horario ya usado queda bloqueado
            ts = await pg.evaluate("[...document.querySelectorAll('.r-turno')].map(t=>t.querySelector('.r-horas .chip[aria-pressed=true]')?.textContent)")
            if len(set(ts)) != 3: f.append("se repitió día y horario: " + str(ts))
            if CAPT: await pg.locator(".regalo-hoja").screenshot(path=str(CAPT / "regalo-monto-horarios.png"))
            await datos(pg)
            await pg.wait_for_timeout(1500)
            if "Ya reservamos tus turnos" not in await pg.locator("#regalo").inner_text(): f.append("no llegó al éxito")
        fl, posts = await caso(b, "monto-3-turnos", "AB12-CD34", lambda e: (200, monto(e)),
                               lambda n: (200, {"numero": "0456", "turnos": [{"servicio": "Combo 1", "fecha": "2026-12-10", "hora": "09:40"}] * 3}), p_monto)
        total += len(fl)
        if posts and len(posts[0].get("turnos", [])) != 3: print("FALLA: el canje por monto no mandó 3 turnos"); total += 1

        for nombre, st, body, esperado in [("no-existe", 404, {}, "No encontramos este regalo"),
                                           ("canjeado", 410, {"estado": "canjeado"}, "ya se usó"),
                                           ("vencido", 410, {"estado": "vencido"}, "venció"),
                                           ("anulado", 410, {"estado": "anulado"}, "no está disponible"),
                                           ("intentos", 429, {}, "Esperá unos minutos")]:
            async def p_est(pg, f, esperado=esperado):
                if esperado not in await pg.locator("#regalo").inner_text(): f.append("falta: " + esperado)
                if not await pg.locator("#regalo a[href*='wa.me']").count(): f.append("falta el botón para escribirle a Flor")
            fl, _ = await caso(b, nombre, "ZZZZ-9999", lambda e, st=st, body=body: (st, body), None, p_est); total += len(fl)

        async def p_409(pg, f):
            await pg.click("#regalo >> text=Elegir día y horario"); await elegir_turno(pg); await datos(pg)
            await pg.wait_for_timeout(600)
            txt = await pg.locator("#regalo").inner_text()
            if "se acaba de ocupar" not in txt or "Elegí día y horario" not in txt: f.append("el 409 no volvió a elegir horario")
        fl, _ = await caso(b, "horario-tomado", "K7P2-9XQM", lambda e: (200, COMBO), lambda n: (409, {"error": "Ese horario se acaba de ocupar. Elegí otro, por favor."}), p_409)
        total += len(fl)

        async def p_sin(pg, f):
            await pg.click("#regalo >> text=Elegir día y horario"); await elegir_turno(pg); await datos(pg, tildar=False)
            if await pg.locator("#regalo >> text=Ya reservamos").count(): f.append("confirmó sin consentimiento")
        fl, posts = await caso(b, "sin-consentimiento", "K7P2-9XQM", lambda e: (200, COMBO), lambda n: (200, {}), p_sin)
        total += len(fl) + (1 if posts else 0)
        if posts: print("FALLA: envió el canje sin consentimiento")

        fl, _ = await caso(b, "combo-compu", "K7P2-9XQM", lambda e: (200, COMBO), None, None, w=1366); total += len(fl)
        await b.close()
    print("\nSin fallas." if not total else f"\n{total} fallas.")
    sys.exit(1 if total else 0)


asyncio.run(main())
