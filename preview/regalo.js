/* ===== Regalo: canje de vouchers de NEO Gestión (?regalo=<código>) =====
   Regla de oro: es un regalo. Nunca se muestran montos, saldo ni precios.
   NEO resuelve la lógica; la landing solo consulta y envía. */
(() => {
  const NEO = "https://neo-gestion.vercel.app/api/publico";
  const SLUG = "silkderma";
  // Cloudflare Turnstile: site key pública del widget creado para el dominio de la landing.
  // La secret key va solo en NEO (Vercel), nunca acá.
  const TURNSTILE_SITEKEY = "0x4AAAAAAF2kMUOYYvqCVUrH";
  let WA = "5493775445169";

  const $ = id => document.getElementById(id);
  const el = (tag, props = {}, ...hijos) => { const e = document.createElement(tag); Object.assign(e, props); hijos.forEach(h => e.append(h)); return e; };
  const waLink = txt => "https://wa.me/" + WA + "?text=" + encodeURIComponent(txt);
  const fecha = s => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
  const fDia = new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long" });
  const fLargo = new Intl.DateTimeFormat("es-AR", { day: "numeric", month: "long" });
  // Nombre del combo con su categoría si NEO la manda ("Combo 1 · Mujeres")
  const nom = s => s.nombre + (s.categoria ? " · " + s.categoria : "");
  const diaTxt = s => { const x = fDia.format(fecha(s)).replace(",", ""); return x.charAt(0).toUpperCase() + x.slice(1); };

  // Código: con o sin guion, mayúsculas o minúsculas → "K7P2-9XQM"
  const param = new URLSearchParams(location.search).get("regalo");
  if (param === null) return;
  const limpio = param.toUpperCase().replace(/[^A-Z0-9]/g, "");
  const CODIGO = limpio.length === 8 ? limpio.slice(0, 4) + "-" + limpio.slice(4) : limpio;

  const caja = $("regalo"), pant = $("regaloPantalla");
  let V = null, elegidos = [], agenda = [], turnos = [], tsToken = "", tsId = null;

  const abrir = () => { caja.hidden = false; document.documentElement.classList.add("con-regalo"); caja.focus(); };
  $("regaloCerrar").addEventListener("click", () => { caja.hidden = true; document.documentElement.classList.remove("con-regalo"); history.replaceState(null, "", location.pathname); });

  const pedir = async (url, opc = {}) => {
    const ctl = "AbortController" in window ? new AbortController() : null;
    const t = setTimeout(() => ctl && ctl.abort(), 12000);
    try {
      const r = await fetch(url, { cache: "no-store", signal: ctl ? ctl.signal : undefined, ...opc });
      let d = null; try { d = await r.json(); } catch (_) {}
      return { status: r.status, d };
    } catch (_) { return { status: 0, d: null }; } finally { clearTimeout(t); }
  };

  /* ---------- piezas visuales ---------- */
  const regaloSVG = (abierto) => {
    const s = el("div", { className: "regalo-ico" + (abierto ? " abre" : "") });
    s.innerHTML = '<svg viewBox="0 0 120 120" aria-hidden="true"><rect x="22" y="58" width="76" height="50" rx="6" fill="#74956F"/><rect x="54" y="58" width="12" height="50" fill="#D9B35C"/>' +
      '<g class="tapa"><rect x="16" y="44" width="88" height="18" rx="5" fill="#4E6B49"/><rect x="54" y="44" width="12" height="18" fill="#D9B35C"/>' +
      '<path d="M60 44c-6-14-24-20-26-9-2 8 13 9 26 9zM60 44c6-14 24-20 26-9 2 8-13 9-26 9z" fill="#E8C774"/><circle cx="60" cy="44" r="5" fill="#D9B35C"/></g>' +
      '<g class="chispas" fill="#E8C774"><circle cx="30" cy="30" r="3"/><circle cx="92" cy="26" r="3.5"/><circle cx="60" cy="14" r="2.5"/><circle cx="100" cy="50" r="2"/><circle cx="20" cy="52" r="2"/></g></svg>';
    return s;
  };
  const boton = (txt, fn, clase = "btn") => { const b = el("button", { type: "button", className: clase }, txt); b.addEventListener("click", fn); return b; };
  const ayuda = (txt = "Escribirle a Flor") => el("a", { className: "btn btn-sec", href: waLink("Hola Flor! Tengo una consulta sobre mi regalo " + CODIGO + "."), target: "_blank", rel: "noopener noreferrer" }, txt);
  const pantalla = (...hijos) => { pant.replaceChildren(...hijos); pant.scrollTop = 0; caja.scrollTop = 0; };

  const voucher = () => {
    const v = el("div", { className: "voucher " + (V.tipo === "monto" ? "v-monto" : "v-combo") });
    v.innerHTML = '<svg class="v-mono" viewBox="0 0 120 120" aria-hidden="true"><path d="M60 8c-10 20-34 24-52 22 2 20 18 30 52 30s50-10 52-30c-18 2-42-2-52-22z" fill="#D9B35C"/></svg>';
    const cab = el("div", { className: "v-cab" }, el("span", { className: "v-marca" }, "Silkderma"), el("span", { className: "v-num" }, "N.º " + V.numero));
    const cuerpo = el("div", { className: "v-cuerpo" });
    cuerpo.append(el("span", { className: "v-eti" }, "Regalo · Depi Day"));
    if (V.para) cuerpo.append(el("p", { className: "v-linea" }, el("small", {}, "Para"), " " + V.para));
    if (V.de) cuerpo.append(el("p", { className: "v-linea" }, el("small", {}, "De"), " " + V.de));
    if (V.mensaje) cuerpo.append(el("blockquote", {}, "“" + V.mensaje + "”"));
    cuerpo.append(el("p", { className: "v-que" }, V.tipo === "combo" && V.servicio ? nom(V.servicio) : "Combos a elección"));
    const pie = el("div", { className: "v-pie" }, "Válido hasta el " + fLargo.format(fecha(V.vence)));
    v.append(cab, cuerpo, pie);
    return v;
  };

  /* ---------- estados ---------- */
  const ESTADOS = {
    canjeado: ["Este regalo ya se usó", "Si tenés dudas sobre tu turno, escribile a Flor."],
    vencido: ["Este regalo venció", "Escribile a Flor y vemos cómo te ayudamos."],
    anulado: ["Este voucher no está disponible", "Escribile a Flor para consultarlo."],
    noexiste: ["No encontramos este regalo", "Revisá el link que te llegó o escribile a Flor."],
    intentos: ["Esperá unos minutos", "Hubo demasiados intentos. Probá de nuevo en un rato."],
    red: ["No pudimos cargar tu regalo", "Revisá tu conexión y probá de nuevo."],
  };
  const estado = (k, extra) => {
    const [t, p] = ESTADOS[k];
    const titulo = k === "vencido" && extra ? "Este regalo venció el " + fLargo.format(fecha(extra)) : t;
    const hijos = [regaloSVG(false), el("h2", {}, titulo), el("p", {}, p), el("div", { className: "r-acciones" }, ayuda())];
    if (k === "red" || k === "intentos") hijos[3].prepend(boton("Probar de nuevo", cargar));
    pantalla(el("div", { className: "r-estado r-" + k }, ...hijos));
  };
  const cargando = () => pantalla(el("div", { className: "r-cargando", role: "status" },
    el("div", { className: "sk sk-card" }), el("div", { className: "sk sk-linea" }), el("div", { className: "sk sk-linea corta" }), el("span", { className: "sr" }, "Cargando tu regalo…")));

  /* ---------- 1) bienvenida ---------- */
  const consultar = async () => {
    const q = elegidos.length ? "?elegidos=" + elegidos.map(e => encodeURIComponent(e.id)).join(",") : "";
    return pedir(NEO + "/vouchers/" + SLUG + "/" + encodeURIComponent(CODIGO) + q);
  };
  const manejarError = (r) => {
    if (r.status === 404) return estado("noexiste");
    if (r.status === 410) return estado(r.d && ESTADOS[r.d.estado] ? r.d.estado : "canjeado", r.d && r.d.vence);
    if (r.status === 429) return estado("intentos");
    return estado("red");
  };
  const cargar = async () => {
    if (!/^[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(CODIGO)) return estado("noexiste");
    cargando();
    const [r, a] = await Promise.all([consultar(), pedir(NEO + "/turnos/" + SLUG)]);
    if (r.status !== 200 || !r.d) return manejarError(r);
    V = r.d;
    if (a.status === 200 && a.d && Array.isArray(a.d.dias)) { agenda = a.d.dias; if (/^\d{8,15}$/.test(a.d.whatsapp || "")) WA = a.d.whatsapp; }
    bienvenida();
  };
  const saludo = () => {
    const h = el("h2", { className: "r-titulo" }, (V.para ? V.para + ", ¡te" : "¡Te") + " regalaron un Depi Day!");
    return [el("span", { className: "eyebrow" }, "Tenés un regalo"), h];
  };
  const bienvenida = () => {
    const partes = [...saludo(), voucher()];
    if (V.tipo === "combo" && V.servicio) {
      elegidos = [V.servicio];
      partes.push(el("div", { className: "r-combo" }, el("b", {}, nom(V.servicio)), el("span", {}, (V.servicio.zonas || []).join(" · "))),
        el("div", { className: "r-acciones" }, boton("Elegir día y horario", () => { turnos = [{ s: V.servicio }]; paso2(); })));
    } else partes.push(el("div", { id: "rCombos" }));
    pantalla(el("div", { className: "r-bienvenida" }, ...partes));
    if (V.tipo !== "combo") pintarCombos();
  };

  /* Por monto: agregar y quitar combos (se puede repetir); la lista la decide NEO */
  const pintarCombos = () => {
    const c = $("rCombos"); if (!c) return;
    const disp = V.servicios_disponibles || [];
    const lista = el("div", { className: "r-lista" });
    disp.forEach(s => {
      const b = boton("Agregar", () => cambiar(() => elegidos.push(s)), "btn btn-chico");
      b.disabled = elegidos.length >= 10;
      lista.append(el("div", { className: "r-op" }, el("div", {}, el("b", {}, nom(s)), el("span", {}, (s.zonas || []).join(" · "))), b));
    });
    const res = el("div", { className: "r-resumen" });
    if (elegidos.length) {
      res.append(el("b", {}, "Tu elección"));
      elegidos.forEach((s, i) => res.append(el("div", { className: "r-chip" }, el("span", {}, nom(s)), boton("Quitar", () => cambiar(() => elegidos.splice(i, 1)), "r-quitar"))));
    }
    const hijos = [el("h3", {}, "Elegí tus combos"), el("p", { className: "r-sub" }, disp.length ? "Están incluidos en tu regalo. Podés sumar más de uno." : "¡Ya elegiste todo lo que incluye tu regalo!"), lista, res];
    if (elegidos.length) hijos.push(el("div", { className: "r-acciones" }, boton(elegidos.length > 1 ? "Elegir días y horarios" : "Elegir día y horario", () => { turnos = elegidos.map(s => ({ s })); paso2(); })));
    c.replaceChildren(...hijos);
  };
  const cambiar = async (fn) => {
    fn(); const c = $("rCombos"); c.classList.add("cargando-lista");
    const r = await consultar(); c.classList.remove("cargando-lista");
    if (r.status !== 200 || !r.d) return manejarError(r);
    V.servicios_disponibles = r.d.servicios_disponibles || [];
    pintarCombos();
  };

  /* ---------- 2) día y horario por cada combo ---------- */
  const libres = d => d.horarios.filter(h => !(d.ocupados || []).includes(h));
  const tomado = (f, h, i) => turnos.some((t, j) => j !== i && t.fecha === f && t.hora === h);
  const paso2 = () => {
    const dias = agenda.filter(d => !V.vence || d.fecha <= V.vence).filter(d => libres(d).length);
    const bloques = turnos.map((t, i) => {
      const b = el("div", { className: "r-turno" });
      b.append(el("h4", {}, (turnos.length > 1 ? (i + 1) + ". " : "") + nom(t.s)));
      const tira = el("div", { className: "r-dias" });
      dias.forEach(d => {
        const btn = boton("", () => { t.fecha = d.fecha; t.hora = null; paso2(); }, "r-dia");
        const f = fecha(d.fecha);
        btn.append(el("small", {}, new Intl.DateTimeFormat("es-AR", { weekday: "short" }).format(f)), el("b", {}, String(f.getDate())), el("small", {}, new Intl.DateTimeFormat("es-AR", { month: "short" }).format(f)));
        btn.setAttribute("aria-pressed", String(t.fecha === d.fecha)); tira.append(btn);
      });
      b.append(tira);
      const d = dias.find(x => x.fecha === t.fecha);
      if (d) {
        const hs = el("div", { className: "r-horas" });
        libres(d).forEach(h => { const hb = boton(h, () => { t.hora = h; paso2(); }, "chip"); hb.disabled = tomado(d.fecha, h, i); hb.setAttribute("aria-pressed", String(t.hora === h)); hs.append(hb); });
        b.append(hs);
      } else b.append(el("p", { className: "r-sub" }, "Elegí un día para ver los horarios libres."));
      return b;
    });
    const listo = turnos.every(t => t.fecha && t.hora);
    const avance = boton("Seguir", paso3); avance.disabled = !listo;
    const vacio = !dias.length ? [el("p", { className: "r-aviso" }, "Ahora no hay días con horarios libres. Escribile a Flor y lo coordinan."), el("div", { className: "r-acciones" }, ayuda())] : [];
    pantalla(el("div", { className: "r-paso" }, el("span", { className: "eyebrow" }, "Paso 1 de 2"), el("h2", {}, turnos.length > 1 ? "Elegí días y horarios" : "Elegí día y horario"),
      ...(vacio.length ? vacio : bloques), el("div", { className: "r-acciones" }, boton("Volver", bienvenida, "btn btn-sec"), avance)));
  };

  /* ---------- 3) datos y confirmación ---------- */
  const resumen = () => el("ul", { className: "r-res" }, ...turnos.map(t => el("li", {}, el("b", {}, diaTxt(t.fecha) + ", " + t.hora), " · " + nom(t.s))));
  const paso3 = (aviso) => {
    const f = el("form", { className: "r-form", noValidate: true });
    f.append(
      el("label", {}, "Nombre y apellido", el("input", { name: "nombre", required: true, maxLength: 60, autocomplete: "name" })),
      el("label", {}, "WhatsApp", el("input", { name: "telefono", type: "tel", required: true, maxLength: 20, pattern: "\\+?[0-9 ]{8,20}", autocomplete: "tel", placeholder: "Ej. 3775 123456" })),
      el("label", { className: "r-check" }, el("input", { type: "checkbox", name: "ok", required: true }), el("span", {}, "Acepto que Silkderma guarde mi nombre y WhatsApp para gestionar mi turno.")),
      el("div", { id: "rTurnstile", className: "r-ts" }),
      el("p", { className: "r-error", id: "rError", role: "alert", hidden: true }),
      el("div", { className: "r-acciones" }, boton("Volver", paso2, "btn btn-sec"), el("button", { type: "submit", className: "btn", id: "rEnviar" }, turnos.length > 1 ? "Confirmar mis turnos" : "Confirmar mi turno")));
    f.addEventListener("submit", e => { e.preventDefault(); enviar(f); });
    const hijos = [el("span", { className: "eyebrow" }, "Paso 2 de 2"), el("h2", {}, "Tus datos"), resumen(), f];
    if (aviso) hijos.splice(2, 0, el("p", { className: "r-aviso" }, aviso));
    pantalla(el("div", { className: "r-paso" }, ...hijos));
    turnstile();
  };
  const turnstile = () => {
    tsToken = "";
    const cont = $("rTurnstile"); if (!cont) return;
    if (!TURNSTILE_SITEKEY) { cont.hidden = true; return; } // sin clave configurada (vista previa)
    const pintar = () => { tsId = window.turnstile.render(cont, { sitekey: TURNSTILE_SITEKEY, language: "es", callback: t => { tsToken = t; }, "expired-callback": () => { tsToken = ""; } }); };
    if (window.turnstile) return pintar();
    window.onTurnstileLoad = pintar;
    if (!document.querySelector("script[data-ts]")) {
      const s = el("script", { src: "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad&render=explicit", async: true, defer: true }); s.dataset.ts = "1"; document.head.append(s);
    }
  };
  const enviar = async (f) => {
    const err = $("rError"); err.hidden = true;
    if (!f.reportValidity()) return;
    if (TURNSTILE_SITEKEY && !tsToken) { err.textContent = "Completá la verificación antes de confirmar."; err.hidden = false; return; }
    const datos = { nombre: f.elements.nombre.value.trim(), telefono: f.elements.telefono.value.trim(), consentimiento: true, turnstile: tsToken };
    const cuerpo = V.tipo === "combo"
      ? { servicio_id: turnos[0].s.id, fecha: turnos[0].fecha, hora: turnos[0].hora, ...datos }
      : { turnos: turnos.map(t => ({ servicio_id: t.s.id, fecha: t.fecha, hora: t.hora })), ...datos };
    const b = $("rEnviar"); b.disabled = true; b.textContent = "Reservando…";
    const r = await pedir(NEO + "/vouchers/" + SLUG + "/" + encodeURIComponent(CODIGO) + "/canjear", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
    if (r.status === 200 && r.d) return exito(r.d);
    if (r.status === 409) {
      const a = await pedir(NEO + "/turnos/" + SLUG); if (a.status === 200 && a.d && Array.isArray(a.d.dias)) agenda = a.d.dias;
      turnos.forEach(t => { const d = agenda.find(x => x.fecha === t.fecha); if (!d || !libres(d).includes(t.hora)) t.hora = null; });
      paso2(); pant.prepend(el("p", { className: "r-aviso" }, (r.d && r.d.error) || "Ese horario se acaba de ocupar. Elegí otro, por favor."));
      return;
    }
    if (r.status === 404 || r.status === 410 || r.status === 429) return manejarError(r);
    if (window.turnstile && tsId !== null) window.turnstile.reset(tsId);
    err.textContent = (r.d && r.d.error) || "No pudimos confirmar tu turno. Probá de nuevo o escribile a Flor.";
    err.hidden = false; b.disabled = false; b.textContent = turnos.length > 1 ? "Confirmar mis turnos" : "Confirmar mi turno";
  };

  /* ---------- 4) éxito ---------- */
  const exito = (d) => {
    const ts = (d.turnos && d.turnos.length ? d.turnos : turnos.map(t => ({ servicio: nom(t.s), fecha: t.fecha, hora: t.hora })));
    const nomS = s => typeof s === "string" ? s : (s && s.nombre ? nom(s) : "");
    const lista = el("ul", { className: "r-res" }, ...ts.map(t => el("li", {}, el("b", {}, diaTxt(t.fecha) + ", " + t.hora), " · " + nomS(t.servicio))));
    pantalla(el("div", { className: "r-estado r-exito" }, regaloSVG(true), el("h2", {}, "¡Listo! " + (ts.length > 1 ? "Ya reservamos tus turnos" : "Ya reservamos tu turno")), lista,
      el("p", {}, "En breve Flor te escribe por WhatsApp para confirmarlo."), el("div", { className: "r-acciones" }, ayuda("¿Dudas? Escribile a Flor"))));
  };

  abrir(); cargar();
})();
