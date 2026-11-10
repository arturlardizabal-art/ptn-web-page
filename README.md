# PTN — landing y servicios

Sitio estático de Parches y Textiles del Norte. Conserva la marca, fuentes y recursos gráficos del sitio existente. La portada y cada servicio entregan HTML completo; JavaScript se usa para el menú y para preparar una solicitud de WhatsApp.

## Trabajar en local

Se requiere Python 3; no hay dependencias npm ni base de datos.

```sh
python3 scripts/dev.py start
python3 scripts/dev.py status
python3 scripts/dev.py stop
```

Vista local: <http://127.0.0.1:3200/>. El servidor escucha solamente en loopback y permanece activo hasta ejecutar `stop`. Los logs y PID están en `.local/`, excluido de Git. La vista añade `X-Robots-Tag: noindex, nofollow` y recarga el navegador al cambiar contenido o estilos. Ese encabezado es exclusivo del servidor de desarrollo.

## Editar

- `content/site.json`: identidad, contactos y directorios de marcas/clientes.
- `content/services.json`: 13 servicios, contenido ES/EN, recursos y relacionados.
- `content/seo-plan.json`: familias de búsqueda y prioridades propuestas, sin volúmenes medidos.
- `scripts/build.py`: generación de portada, páginas de apoyo y servicios.
- `assets/site.css` y `assets/site.js`: diseño e interacciones.
- `assets/media/`: versiones WebP optimizadas de los recursos existentes. Los originales siguen en `assets/bundle/`.

Las páginas HTML, sitemap y CSV se generan desde esas fuentes. No editar directamente un HTML generado: el siguiente build lo reemplazará.

```sh
python3 scripts/build.py
python3 scripts/check.py
```

El check HTTP requiere el servidor local activo y revisa 38 páginas, sitemap, recursos, canonical, hreflang, enlaces y 404. `--base` permite revisar otro origen, aunque el chequeo de carpetas ocultas está pensado para este servidor local.

## Arquitectura

Español: `/`, `/servicios/`, 13 servicios bajo `/servicios/<slug>/`, `/nosotros/`, `/clientes/`, `/distribuidores/`, `/contacto/`.

Inglés: equivalentes reales bajo `/en/`, con nombres de rutas en inglés. Son 38 páginas indexables; `404.html` y documentos de revisión se excluyen del sitemap. Las versiones ES/EN se enlazan de forma recíproca. No se cambia el idioma por detección del navegador.

`Organization`, `WebSite`, `WebPage`, `BreadcrumbList` y `Service` describen información visible. No hay reseñas, precios ni certificaciones ficticias. Las FAQ visibles ayudan al comprador; no se prometen resultados enriquecidos.

## Contacto y medición

Los CTA del servicio llevan a `/contacto/?servicio=<slug>` y precargan el servicio. El formulario prepara un borrador de WhatsApp, que el visitante debe revisar y enviar. No hay backend ni correo enviado automáticamente. Los contactos directos siguen disponibles sin JavaScript; el botón para preparar el formulario requiere JavaScript.

Los eventos `quote_click`, `whatsapp_click`, `phone_click`, `email_click` y `quote_draft_prepared` se agregan a `dataLayer` con servicio, idioma y página. No incluyen los datos del formulario y no se consideran un lead confirmado. Para medir tráfico hace falta conectar una propiedad real de analítica; no se agregó un identificador ficticio.

## Revisión SEO/GEO

- Informe local: <http://127.0.0.1:3200/docs/analisis-seo-geo.html>.
- Documento: `docs/analisis-seo-geo.html`.
- Mapa editable: `docs/mapa-servicios-seo-geo.csv`.

Antes de publicar, confirmar contactos, dirección, horarios, alcance comercial, marcas/clientes y derechos de imágenes; las afirmaciones se basan en el sitio existente. Verificar el hosting real, Search Console, Bing y analítica después del lanzamiento. El flujo de publicación usa GitHub Pages desde `main`; las vistas locales permanecen disponibles para seguir trabajando.

## Publicación existente

El repositorio sirve archivos desde raíz mediante GitHub Pages con el dominio de `CNAME`: `ptntextiles.com`. `.nojekyll` se conserva. Los HTML generados están listos para ese formato; no se registró otro hosting ni se alteró el dominio. El servidor de desarrollo no forma parte del entorno de producción.
