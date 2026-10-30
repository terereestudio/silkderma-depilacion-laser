# Silkderma · Depilación láser

Landing de Silkderma (Florencia Vich, Monte Caseros). Desarrollado por Tereré Estudio.

- `index.html`: la página publicada. Netlify sirve este archivo desde la raíz de `main` (cada cambio en `main` se publica solo).
- `preview/`: fuente de la página (`template.html`), imágenes y `build.py`, que arma `index.html`.
- `material/`: fotos y capturas del cliente.

La versión final queda en la raíz (no se usa `sitio/`). Los archivos de servidor que falten (`_headers` con CSP, política de privacidad, `/gracias/`) también van en la raíz. La CSP tiene que permitir `connect-src https://neo-gestion.vercel.app`.

## Turnero conectado a NEO Gestión
Los combos, días y horarios se leen en vivo de NEO Gestión (`NEO_URL` en `preview/template.html`). Flor los edita desde la app, en Turnos. La página no escribe nada en NEO.

### Cómo se ve con cualquier cantidad de días (ya programado)
- **Qué días se muestran:** solo los que no pasaron y tienen al menos un horario. Se ordenan y se quitan repetidos aunque NEO los mande desordenados. Nada se inventa ni se rellena.
- **Tira horizontal:** en celular se ven 2 días y medio y se desliza; en compu se ven 7 (una semana) y las flechas avanzan de a una semana. La altura es siempre la misma, sean 2 días o 400.
- **Chips de mes:** si los días abiertos son de 2 meses o más. Si un mes se repite (agenda de más de un año), suma el año: "Octubre 2026 … Octubre 2027".
- **Chips de semana:** para el mes que se está viendo, si ese mes tiene más de 10 días abiertos: "1 al 7 nov", "8 al 14 nov", etc. (rango real de días abiertos). Cambian solos al pasar de mes.
- **Encabezado:** eyebrow con el mes o los meses ("Noviembre · Monte Caseros", "Noviembre y diciembre · …", "Noviembre a enero · …"). Texto: 1 día / hasta 7 días / un mes / varios meses. "Depi Days" no cambia.
- **Sin días abiertos:** tarjeta "Por ahora no hay Depi Days abiertos" con botón a WhatsApp. **Todos completos:** aviso para anotarse por WhatsApp. Los días completos se ven apagados, no se ocultan.
- **Mientras carga:** tarjetas vacías ("Cargando turnos…") en el turnero y en los combos. Se pinta una sola vez: con NEO, o con el respaldo si NEO falla, responde 404, manda datos inválidos o tarda más de 5 segundos.
- **Respaldo:** los días, horarios y combos escritos en el código son la agenda real de los Depi Days de noviembre. Se quitan cuando la agenda esté activa y estable en NEO (después del 9/11); ahí, si NEO falla, se muestra un mensaje para escribir por WhatsApp con botón de reintentar.

### Pruebas
`python3 preview/build.py && python3 preview/pruebas_turnero.py` simula NEO con 0, 1, 2, 7, 12, 28, 60, 180 y 400 días, todos completos, datos desordenados o repetidos, días sin horarios, sin servicios, datos inválidos, 404, NEO caído y colgado, en 360, 390 y 1366 px. Correrlo antes de cada merge a `main`.

Después de editar `template.html`: `python3 preview/build.py`.
