# Silkderma · Depilación láser

Landing de Silkderma (Florencia Vich, Monte Caseros). Desarrollado por Tereré Estudio.

- `index.html`: vista previa actual (borrador, horarios de ejemplo).
- `preview/`: fuente de la vista previa (`template.html`) e imágenes.
- `material/`: fotos y capturas del cliente.

La versión final irá en `sitio/`, lista para Netlify.

## Turnero conectado a NEO Gestión
Los combos, días y horarios se leen en vivo de NEO Gestión (`NEO_URL` en `preview/template.html`). Flor los edita desde la app, en Turnos. Si NEO no responde o la agenda no está activada, el turnero usa los datos escritos en el código.

Después de editar `template.html`: `python3 preview/build.py`.
