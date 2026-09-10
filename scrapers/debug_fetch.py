"""
Herramienta de diagnóstico -- úsala si alguna tienda sigue saliendo
"not-found" y quieres ver qué está devolviendo la página realmente.

Uso:
    python -m scrapers.debug_fetch "https://www.walmart.com.mx/ip/..."
"""
import re
import sys

from .scraperapi_client import fetch_html


def debug(url: str):
    html = fetch_html(url)

    with open("debug_output.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML guardado en debug_output.html ({len(html)} caracteres)")

    print("\n--- PRIMEROS 1500 CARACTERES DEL HTML ---")
    print(html[:1500])
    print("--- FIN DEL EXTRACTO ---\n")

    price_pattern = re.compile(r'[\$]\s?\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?')
    matches = price_pattern.findall(html)
    print(f"\nPatrones tipo '$XXX.XX' encontrados en el HTML: {len(matches)}")
    for m in matches[:15]:
        print(f"  {m}")

    meta_pattern = re.compile(r'<meta[^>]+price[^>]*>', re.IGNORECASE)
    meta_matches = meta_pattern.findall(html)
    print(f"\nMetaetiquetas con 'price': {len(meta_matches)}")
    for m in meta_matches[:10]:
        print(f"  {m}")

    jsonld_count = html.count('application/ld+json')
    print(f"\nBloques JSON-LD encontrados: {jsonld_count}")


if __name__ == "__main__":
    debug(sys.argv[1])
