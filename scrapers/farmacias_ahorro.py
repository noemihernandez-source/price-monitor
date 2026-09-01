"""
Scraper de Farmacias del Ahorro.

Muchos sitios de farmacias/retail en México corren sobre VTEX, que
normalmente sí incluye JSON-LD de producto (lo usan para Google Shopping).
Por eso este scraper prioriza esa vía y cae a selectores CSS solo si falla.

CALIBRACIÓN REQUERIDA: igual que con Walmart, valida FALLBACK_SELECTORS
contra una página real antes de confiar en el resultado en producción.
"""
import asyncio
import sys

from .common import PriceResult, extract_price_from_jsonld, extract_price_from_selectors, fetch_rendered_html

FALLBACK_SELECTORS = [
    ".vtex-product-price-1-x-sellingPrice",
    ".vtex-store-components-3-x-sellingPrice",
    '[class*="sellingPrice"]',
    '[class*="price"]',
]


async def get_price(url: str) -> PriceResult:
    html = await fetch_rendered_html(url, wait_selector="main, body")
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
