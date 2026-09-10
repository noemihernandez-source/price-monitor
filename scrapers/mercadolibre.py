"""
Mercado Libre SÍ tiene una API pública oficial y gratuita, así que aquí no
hace falta scraping (es más rápido, más estable y no hay riesgo de bloqueo).

Dos formas de usarla:
1. Por ID de publicación (RECOMENDADO): si ya conoces la URL del producto,
   el ID es la parte "MLM1234567890". Esto es exacto.
2. Por búsqueda de texto (fallback): usa el nombre del producto.

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
        # Distinguimos el motivo real del fallo en vez de un "not-found" ciego.
        # Si es 401/403, muy probablemente ML ya exige autenticación (token
        # OAuth) para este endpoint, no que el producto no exista.
        motivo = f"http-{resp.status_code}"
        return PriceResult(price=None, currency="MXN", in_stock=None, method=motivo, raw_snippet=resp.text[:200])
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
        motivo = f"http-{resp.status_code}"
        return PriceResult(price=None, currency="MXN", in_stock=None, method=motivo, raw_snippet=resp.text[:200])
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
