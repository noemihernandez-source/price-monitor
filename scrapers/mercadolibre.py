"""
Mercado Libre SÍ tiene una API pública oficial y gratuita, así que aquí no
hace falta scraping (es más rápido, más estable y no hay riesgo de bloqueo).

Dos formas de usarla:
1. Por ID de publicación (RECOMENDADO): si ya conoces la URL del producto
   (ej. https://articulo.mercadolibre.com.mx/MLM-1234567890-...), el ID es
   la parte "MLM1234567890". Esto es exacto: siempre trae el mismo producto.
2. Por búsqueda de texto (fallback): usa el nombre del producto. Es más
   ambiguo -- Mercado Libre puede tener 20 vendedores distintos del mismo
   producto con precios distintos. Por default devolvemos el precio más bajo
   entre los primeros resultados, que es justo lo que le importa a Amazon.

Docs: https://developers.mercadolibre.com.mx/
"""
import re
import sys

import requests

from .common import PriceResult

API_BASE = "https://api.mercadolibre.com"


def _extract_item_id(url_or_id: str) -> str | None:
    match = re.search(r"(MLM-?\d{6,})", url_or_id.upper())
    if not match:
        return None
    return match.group(1).replace("-", "")


def get_price_by_item_id(item_id: str) -> PriceResult:
    resp = requests.get(f"{API_BASE}/items/{item_id}", timeout=15)
    if resp.status_code != 200:
        return PriceResult(price=None, currency="MXN", in_stock=None, method="not-found")
    data = resp.json()
    return PriceResult(
        price=data.get("price"),
        currency=data.get("currency_id", "MXN"),
        in_stock=data.get("available_quantity", 0) > 0,
        method="api",
        raw_snippet=data.get("permalink", ""),
    )


def get_lowest_price_by_search(query: str, site: str = "MLM") -> PriceResult:
    resp = requests.get(
        f"{API_BASE}/sites/{site}/search",
        params={"q": query, "limit": 10},
        timeout=15,
    )
    if resp.status_code != 200:
        return PriceResult(price=None, currency="MXN", in_stock=None, method="not-found")
    results = resp.json().get("results", [])
    if not results:
        return PriceResult(price=None, currency="MXN", in_stock=None, method="not-found")
    cheapest = min(results, key=lambda r: r.get("price", float("inf")))
    return PriceResult(
        price=cheapest.get("price"),
        currency=cheapest.get("currency_id", "MXN"),
        in_stock=cheapest.get("available_quantity", 0) > 0,
        method="api",
        raw_snippet=cheapest.get("permalink", ""),
    )


def get_price(url_or_query: str) -> PriceResult:
    """Punto de entrada único: detecta si le pasaron un ID/URL de ML o un texto de búsqueda."""
    if not url_or_query or url_or_query.strip().upper() in ("PENDIENTE", ""):
        return PriceResult(price=None, currency="MXN", in_stock=None, method="sin-url")
    item_id = _extract_item_id(url_or_query)
    if item_id:
        return get_price_by_item_id(item_id)
    return get_lowest_price_by_search(url_or_query)


if __name__ == "__main__":
    print(get_price(sys.argv[1]))
