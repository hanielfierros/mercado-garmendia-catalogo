# Mercado Garmendia — Catálogo Público (Ligero)

Catálogo estático de locales y productos del **Mercado Garmendia** (Culiacán,
Sinaloa). Sitio ligero orientado a GitHub Pages y descubrimiento por
Google Search / AI.

- HTML5 + CSS3 + JavaScript vanilla (sin frameworks).
- PWA mínima (manifest + service worker).
- SEO: HTML crawlable, JSON-LD `Product`/`Offer` y `LocalBusiness` (solo datos reales).
- Búsqueda local sobre `search-index.json` (sin servidor).

## Fuente de datos

`../Base de Datos/mercado_garmendia.json`

La fuente es de solo lectura. El generador **no la modifica** y **no fabrica**
datos: si un campo no existe (categoría, imagen, GTIN/MPN, marca, rating,
disponibilidad), simplemente se omite.

## Generar el sitio

```bash
cd "WEB Publica catalogo LIGERA"
python generate_catalog.py
```

Esto lee el JSON y genera:

- `index.html` (inicio + búsqueda)
- `/locales/index.html` y `/locales/<slug>/index.html` (250 locales)
- `/productos/<slug>/index.html` (6494 productos)
- `search-index.json` (índice mínimo para búsqueda)
- `sitemap.xml` (todas las URLs)

## Estructura

```
/
├── index.html            # inicio
├── styles.css            # estilos
├── app.js                # búsqueda local
├── manifest.json         # PWA
├── sw.js                 # service worker (solo estáticos)
├── robots.txt            # allow all
├── sitemap.xml           # generado
├── search-index.json     # generado
├── garmen-2.jpg          # logo
├── generate_catalog.py   # generador
├── locales/<slug>/index.html
└── productos/<slug>/index.html
```

> No hay `/categorias/` porque la fuente no contiene un campo de categoría.

## Ejecutar localmente

```bash
python -m http.server 8080
# http://localhost:8080/
```

## Publicar en GitHub Pages

1. Sube la carpeta a un repositorio (los archivos generados en la raíz).
2. `Settings → Pages → Branch: main → Save`.
3. Ajusta `SITE_BASE_URL` en `generate_catalog.py` a
   `https://<usuario>.github.io/<repositorio>` y regenera antes de publicar.

## Notas de seguridad

- Sin API keys, tokens ni secretos en el proyecto.
- Sin modificación de la API, del Checkout ni de la base de datos.
- El service worker solo cachea recursos estáticos (no datos personales ni de pedidos).

## Limitaciones (MVP)

- El icono del manifest usa `garmen-2.jpg` (no cuadrado); para instalación PWA
  completa se recomiendan iconos PNG cuadrados (192 y 512 px).
