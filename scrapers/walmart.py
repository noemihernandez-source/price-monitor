"""
Scraper de Walmart México.

Walmart MX es una SPA (React/Next.js), por lo que el precio no está en el
HTML inicial: hay que renderizar con Playwright. Primero intenta leer el
precio desde datos estructurados JSON-LD; si el sitio no los trae en esa
página, cae a selectores CSS de respaldo.

CALIBRACIÓN REQUERIDA: los selectores de FALLBACK_SELECTORS son candidatos
razonables basados en patrones comunes de e-commerce, pero no fueron
verificados contra el HTML real de walmart.com.mx. Correr
`python -m scrapers.walmart <url>` de forma manual la primera vez y ajustar
la lista si el JSON-LD no aparece.
"""
import asyncio
import sys

from .common import PriceResult, extract_price_from_jsonld, extract_price_from_selectors, fetch_rendered_html

FALLBACK_SELECTORS = [
    '[data-testid="price-wrap"]',
    '[data-automation-id="product-price"]',
    "span.price-characteristic",
    ".price-group",
]


async def get_price(url: str) -> PriceResult:
    if not url or url.strip().upper() in ("PENDIENTE", ""):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="sin-url")
    html = await fetch_rendered_html(url, wait_selector='[data-testid="price-wrap"], main')
    result = extract_price_from_jsonld(html)
    if result:
        return result
    result = extract_price_from_selectors(html, FALLBACK_SELECTORS)
    if result:
        return result
    return PriceResult(price=None, currency="MXN", in_stock=None, method="not-found")


if __name__ == "__main__":
    url = sys.argv[1]
    res = asyncio.run(get_price(url))
    print(res)
