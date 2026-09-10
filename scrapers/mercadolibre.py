"""
Scraper de Mercado Libre.

Antes usábamos su API pública sin autenticación, pero dejó de funcionar
(confirmado: devuelve http-403 -- ahora exigen token OAuth para consultar
precios). En vez de meternos a registrar una app y manejar tokens de
autenticación, usamos ScraperAPI (que ya tenemos pagado para Walmart/FDA)
para traer la página del producto directo, y sacamos el precio del HTML
igual que en los otros scrapers.
"""
import asyncio
import re
import sys

from .common import PriceResult, extract_price_from_jsonld, extract_price_from_meta_tags, extract_price_from_selectors
from .scraperapi_client import fetch_html

FALLBACK_SELECTORS = [
    ".andes-money-amount__fraction",
    '[class*="price-tag-fraction"]',
    '[class*="price"]',
]


def _build_search_url(query: str) -> str:
    """Si no tenemos la URL exacta del producto, armamos una URL de
    búsqueda en Mercado Libre con el texto -- menos preciso (puede traer
    el precio del primer resultado, no necesariamente el mismo vendedor
    oficial), pero mejor que nada."""
    slug = query.strip().replace(" ", "-")
    return f"https://listado.mercadolibre.com.mx/{slug}"


async def get_price(url_or_query: str) -> PriceResult:
    if not url_or_query or url_or_query.strip().upper() in ("PENDIENTE", ""):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="sin-url")

    is_direct_url = "mercadolibre.com" in url_or_query.lower()
    target_url = url_or_query if is_direct_url else _build_search_url(url_or_query)

    html = await asyncio.to_thread(fetch_html, target_url)
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
