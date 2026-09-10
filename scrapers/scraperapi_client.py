"""
Cliente para ScraperAPI (https://www.scraperapi.com/).

Reemplaza el acceso directo con Playwright para sitios que bloquean bots
(confirmamos que Walmart México devuelve una página de verificación a
nuestras solicitudes directas). ScraperAPI ya resuelve proxies, renderizado
de JavaScript y bypass de anti-bot -- nosotros solo le pedimos la URL y
recibimos el HTML como si un navegador real hubiera cargado la página.

Requiere la variable de entorno SCRAPERAPI_KEY.
"""
import os

import requests

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")
API_BASE = "https://api.scraperapi.com"


class ScraperAPIError(Exception):
    pass


def fetch_html(url: str, render: bool = True, timeout: int = 70) -> str:
    """Descarga el HTML ya renderizado de `url` a través de ScraperAPI."""
    if not SCRAPERAPI_KEY:
        raise ScraperAPIError(
            "Falta la variable de entorno SCRAPERAPI_KEY. "
            "Consíguela en https://www.scraperapi.com/ tras contratar el plan."
        )
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url": url,
        "render": "true" if render else "false",
        "country_code": "mx",
    }
    resp = requests.get(API_BASE, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.text
