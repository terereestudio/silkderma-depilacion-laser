# Silkderma · Depilación láser

Landing de Silkderma (Florencia Vich, Monte Caseros). Desarrollado por Tereré Estudio.

- `index.html`: la página publicada. Netlify sirve este archivo desde la raíz de `main` (cada cambio en `main` se publica solo).
- `preview/`: fuente de la página (`template.html`), imágenes y `build.py`, que arma `index.html`.
- `material/`: fotos y capturas del cliente.

La versión final queda en la raíz (no se usa `sitio/`). Los archivos de servidor que falten (`_headers` con CSP, política de privacidad, `/gracias/`) también van en la raíz. La CSP tiene que permitir `connect-src https://neo-gestion.vercel.app`.

## Turnero conectado a NEO Gestión
Los combos, días y horarios se leen en vivo de NEO Gestión (`NEO_URL` en `preview/template.html`). Flor los edita desde la app, en Turnos.

- Mientras carga, el turnero y los combos muestran tarjetas vacías ("Cargando turnos…"). Se pinta una sola vez: con los datos de NEO, o con el respaldo si NEO falla, responde 404 o tarda más de 5 segundos.
- Los días se muestran en una tira horizontal con chips de mes (aparecen cuando hay días de dos meses o más). Sirve para cualquier cantidad de días.
- El eyebrow y el texto del encabezado se arman según los días abiertos. "Depi Days" queda fijo.
- Sin días abiertos: tarjeta "Por ahora no hay Depi Days abiertos" con botón a WhatsApp. Todos completos: aviso con botón para anotarse.
- **Respaldo:** los días, horarios y combos escritos en el código son la agenda real de los Depi Days de noviembre. Se quitan cuando la agenda esté activa y estable en NEO (después del 9/11). Ahí, si NEO falla, se muestra un mensaje para escribir por WhatsApp con un botón de reintentar.

Después de editar `template.html`: `python3 preview/build.py`.
