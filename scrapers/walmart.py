"""
Scraper de Walmart México.

Antes usaba Playwright directo, pero Walmart bloquea ese acceso (confirmado:
la respuesta era una página de "Verifica tu identidad", no el producto
real). Ahora usa ScraperAPI, que ya resuelve ese bloqueo por nosotros.
"""
import asyncio
import sys

from .common import PriceResult, extract_price_from_jsonld, extract_price_from_meta_tags, extract_price_from_selectors
from .scraperapi_client import fetch_html

FALLBACK_SELECTORS = [
    '[data-testid="price-wrap"]',
    '[data-automation-id="product-price"]',
    "span.price-characteristic",
    ".price-group",
]


async def get_price(url: str) -> PriceResult:
    if not url or url.strip().upper() in ("PENDIENTE", ""):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="sin-url")
    # fetch_html usa requests (sync) -- lo corremos en un thread para no
    # bloquear el loop de asyncio mientras esperan las otras tiendas.
    html = await asyncio.to_thread(fetch_html, url)
    result = extract_price_from_jsonld(html)
    if result:
        return result
    result = extract_price_from_meta_tags(html)
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
