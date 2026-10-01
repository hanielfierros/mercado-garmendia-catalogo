#!/usr/bin/env python3
"""
Generador del catálogo estático de Mercado Garmendia (GitHub Pages).

Lee `..\\Base de Datos\\mercado_garmendia.json` y genera:
  - /productos/<slug>/index.html  (una página por producto real)
  - /locales/<slug>/index.html     (una página por local real)
  - /locales/index.html            (directorio de locales)
  - index.html                     (inicio + búsqueda local)
  - search-index.json              (índice mínimo para búsqueda)
  - sitemap.xml                    (todas las URLs válidas)

Reglas: solo datos reales del JSON. No se fabrican categorías, GTIN/MPN,
marcas, imágenes, valoraciones ni disponibilidad. Si el JSON no es válido o
falta, se reporta error (no se adivina).
"""

import os
import re
import sys
import json
import html
import unicodedata
import datetime
from urllib.parse import urlparse

# Base del sitio. Ajustar al publicar en GitHub Pages.
SITE_BASE_URL = "https://hanielfierros.github.io/mercado-garmendia-catalogo"
BASE_PATH = urlparse(SITE_BASE_URL).path.rstrip("/") or ""

SRC_JSON = os.path.join("..", "Base de Datos", "mercado_garmendia.json")
OUT_DIR = "."

LOGO = "garmen-2.jpg"
BRAND = "Mercado Garmendia"
CURRENCY = "MXN"


def slugify(s):
    s = str(s).lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"


def money(n):
    return "${:,.2f}".format(float(n))


def esc(s):
    return html.escape(str(s), quote=True)


def path_url(p):
    """URL interna (con subpath de GitHub Pages)."""
    return BASE_PATH + p


def abs_url(p):
    """URL absoluta para canonical/sitemap."""
    return SITE_BASE_URL + p


def load_source():
    if not os.path.exists(SRC_JSON):
        raise SystemExit("ERROR: no existe la fuente " + SRC_JSON)
    with open(SRC_JSON, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list) or not data:
        raise SystemExit("ERROR: la fuente no es una lista no vacía de locales.")
    for loc in data:
        if not all(k in loc for k in ("id", "vendor", "phone", "items")):
            raise SystemExit("ERROR: estructura de local inesperada: %r" % list(loc.keys()))
        for it in loc.get("items", []):
            if not all(k in it for k in ("id", "name", "price", "unit")):
                raise SystemExit("ERROR: estructura de item inesperada: %r" % list(it.keys()))
    return data


def page(title, desc, canonical, body, ld_json=None):
    ld = ""
    if ld_json:
        ld = ('  <script type="application/ld+json">\n'
              + json.dumps(ld_json, ensure_ascii=False)
              + "\n  </script>")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <title>%s</title>\n'
        '  <meta name="description" content="%s">\n'
        '  <link rel="canonical" href="%s">\n'
        '  <link rel="stylesheet" href="%s/styles.css">\n'
        '  <link rel="manifest" href="%s/manifest.json">\n'
        '%s\n'
        '</head>\n<body>\n'
        '  <header class="top">\n'
        '    <a class="brand" href="%s/">\n'
        '      <img src="%s/%s" alt="%s" class="logo">\n'
        '      <span>%s</span>\n'
        '    </a>\n'
        '  </header>\n'
        '  <main class="wrap">\n'
        '%s\n'
        '  </main>\n'
        '  <footer class="foot">\n'
        '    <a href="%s/">%s</a> &middot; Catálogo informativo\n'
        '  </footer>\n'
        '  <script src="%s/app.js" defer></script>\n'
        '</body>\n</html>\n'
    ) % (
        esc(title), esc(desc), esc(canonical),
        BASE_PATH, BASE_PATH, ld,
        BASE_PATH, BASE_PATH, LOGO, esc(BRAND), esc(BRAND),
        body,
        BASE_PATH, esc(BRAND), BASE_PATH,
    )


def generate():
    data = load_source()
    locales = data

    products = []
    seen_slug = {}
    for loc in locales:
        lid = str(loc["id"])
        for it in loc.get("items", []):
            base = slugify(it["name"]) + "-" + slugify(lid)
            slug = base
            k = 2
            while slug in seen_slug:
                slug = base + "-" + str(k)
                k += 1
            seen_slug[slug] = True
            products.append({
                "item_id": str(it["id"]),
                "name": str(it["name"]),
                "price": it["price"],
                "unit": str(it.get("unit") or ""),
                "local_id": lid,
                "vendor": str(loc["vendor"]),
                "slug": slug,
            })

    # ---- Páginas de producto ----
    os.makedirs(os.path.join(OUT_DIR, "productos"), exist_ok=True)
    for p in products:
        local_path = path_url("/locales/%s/" % slugify(p["local_id"]))
        title = "%s — %s | %s" % (p["name"], p["vendor"], BRAND)
        desc = "%s a %s MXN (%s) en %s (%s), %s." % (
            p["name"], money(p["price"]), p["unit"] or "unidad",
            p["vendor"], p["local_id"], BRAND)
        body = (
            '<nav class="crumbs"><a href="%s/">Inicio</a> &rsaquo; '
            '<a href="%s/locales/">Locales</a> &rsaquo; '
            '<a href="%s">%s</a></nav>\n'
            '    <h1>%s</h1>\n'
            '    <p class="price">%s <span>MXN</span>%s</p>\n'
            '    <p class="local">Local: <a href="%s">%s (%s)</a></p>\n'
            '    <p class="sku">Referencia: %s</p>\n'
            '    <p class="back"><a href="%s/">Volver al catálogo</a></p>\n'
        ) % (
            BASE_PATH, BASE_PATH, local_path, esc(p["vendor"]),
            esc(p["name"]),
            money(p["price"]),
            (" / " + esc(p["unit"])) if p["unit"] else "",
            local_path, esc(p["vendor"]), esc(p["local_id"]),
            esc(p["item_id"]),
            BASE_PATH,
        )
        ld = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": p["name"],
            "sku": p["item_id"],
            "offers": {"@type": "Offer", "price": str(p["price"]), "priceCurrency": CURRENCY},
        }
        d = os.path.join(OUT_DIR, "productos", p["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page(title, desc, abs_url("/productos/%s/" % p["slug"]), body, ld))

    # ---- Páginas de local ----
    os.makedirs(os.path.join(OUT_DIR, "locales"), exist_ok=True)
    for loc in locales:
        lid = str(loc["id"])
        slug = slugify(lid)
        items = loc.get("items", [])
        rows = []
        for it in items:
            pslug = slugify(it["name"]) + "-" + slugify(lid)
            rows.append(
                '<li><a href="%s/productos/%s/">%s</a> &middot; %s%s</li>' % (
                    BASE_PATH, pslug, esc(it["name"]), money(it["price"]),
                    (" / " + esc(str(it.get("unit") or ""))) if it.get("unit") else "",
                )
            )
        body = (
            '<nav class="crumbs"><a href="%s/">Inicio</a> &rsaquo; <a href="%s/locales/">Locales</a></nav>\n'
            '    <h1>%s</h1>\n'
            '    <p class="local">Local: %s</p>\n'
            '    <h2>Productos (%d)</h2>\n'
            '    <ul class="plist">\n%s\n    </ul>\n'
        ) % (BASE_PATH, BASE_PATH, esc(loc["vendor"]), esc(lid), len(items),
             "\n".join("      " + r for r in rows))
        ld = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": loc["vendor"],
            "telephone": "+" + str(loc.get("phone") or "").lstrip("+"),
        }
        d = os.path.join(OUT_DIR, "locales", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page("%s (%s) | %s" % (loc["vendor"], lid, BRAND),
                          "%s, local %s en %s. %d productos." % (loc["vendor"], lid, BRAND, len(items)),
                          abs_url("/locales/%s/" % slug), body, ld))

    # ---- Directorio de locales ----
    loc_rows = []
    for loc in locales:
        lid = str(loc["id"])
        slug = slugify(lid)
        loc_rows.append('<li><a href="%s/locales/%s/">%s</a> <span class="muted">(%s)</span></li>' % (
            BASE_PATH, slug, esc(loc["vendor"]), esc(lid)))
    loc_index_body = (
        '<nav class="crumbs"><a href="%s/">Inicio</a> &rsaquo; Locales</nav>\n'
        '    <h1>Locales</h1>\n'
        '    <p class="muted">%d locales en %s</p>\n'
        '    <ul class="plist">\n%s\n    </ul>\n'
    ) % (BASE_PATH, len(locales), esc(BRAND), "\n".join("      " + r for r in loc_rows))
    with open(os.path.join(OUT_DIR, "locales", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("%s — Locales" % BRAND,
                      "Directorio de %d locales de %s." % (len(locales), BRAND),
                      abs_url("/locales/"), loc_index_body))

    # ---- Inicio ----
    total_items = sum(len(l["items"]) for l in locales)
    home_body = (
        '    <section class="hero">\n'
        '      <h1>%s</h1>\n'
        '      <p class="lead">Catálogo de %d locales y %d productos.</p>\n'
        '    </section>\n'
        '    <section class="searchbox">\n'
        '      <input id="q" type="search" placeholder="Buscar producto o local…" autocomplete="off">\n'
        '      <div id="results"></div>\n'
        '    </section>\n'
        '    <section class="links">\n'
        '      <p><a href="%s/locales/">Ver los %d locales</a></p>\n'
        '    </section>\n'
    ) % (esc(BRAND), len(locales), total_items, BASE_PATH, len(locales))
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("%s — Catálogo" % BRAND,
                      "Catálogo de %s: %d locales y %d productos." % (BRAND, len(locales), total_items),
                      abs_url("/"), home_body))

    # ---- search-index.json ----
    idx = [
        {"n": p["name"], "p": p["price"], "u": p["unit"], "v": p["vendor"],
         "l": p["local_id"], "url": path_url("/productos/%s/" % p["slug"])}
        for p in products
    ]
    with open(os.path.join(OUT_DIR, "search-index.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, separators=(",", ":"))

    # ---- sitemap.xml ----
    urls = [abs_url("/"), abs_url("/locales/")]
    urls += [abs_url("/productos/%s/" % p["slug"]) for p in products]
    urls += [abs_url("/locales/%s/" % slugify(str(l["id"]))) for l in locales]
    today = datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append("  <url><loc>%s</loc><lastmod>%s</lastmod></url>" % (esc(u), today))
    lines.append("</urlset>")
    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    return {
        "P": len(products),
        "L": len(locales),
        "C": 0,
        "URL": len(urls),
        "total_items": total_items,
    }


if __name__ == "__main__":
    try:
        stats = generate()
    except SystemExit as e:
        print(e)
        sys.exit(1)
    print("Generación completada.")
    print("P (productos): %d" % stats["P"])
    print("L (locales): %d" % stats["L"])
    print("C (categorías): %d (la fuente no contiene campo de categoría)" % stats["C"])
    print("URL (sitemap): %d" % stats["URL"])
    print("Total items en fuente: %d" % stats["total_items"])
