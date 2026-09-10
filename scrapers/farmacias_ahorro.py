"""
Scraper de Farmacias del Ahorro.

Este sitio ya funcionaba con Playwright directo, pero lo pasamos a
ScraperAPI también por consistencia (una sola forma de obtener HTML en
todo el proyecto, no dos distintas).
"""
import asyncio
import sys

from .common import PriceResult, extract_price_from_jsonld, extract_price_from_meta_tags, extract_price_from_selectors
from .scraperapi_client import fetch_html

FALLBACK_SELECTORS = [
    ".vtex-product-price-1-x-sellingPrice",
    ".vtex-store-components-3-x-sellingPrice",
    '[class*="sellingPrice"]',
    '[class*="price"]',
]


async def get_price(url: str) -> PriceResult:
    if not url or url.strip().upper() in ("PENDIENTE", ""):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="sin-url")
    if url.strip().upper().startswith("N/A"):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="no-vendido-aqui")
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
