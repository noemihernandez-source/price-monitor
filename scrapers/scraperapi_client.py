"""
Cliente para ScraperAPI (https://www.scraperapi.com/).

Reemplaza el acceso directo con Playwright para sitios que bloquean bots
(confirmamos que Walmart México devuelve una página de verificación a
nuestras solicitudes directas). ScraperAPI ya resuelve proxies y bypass
de anti-bot -- nosotros solo le pedimos la URL y recibimos el HTML.

Requiere la variable de entorno SCRAPERAPI_KEY. Consíganla en
https://www.scraperapi.com/ después de contratar el plan.
"""
import os

import requests

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")
API_BASE = "https://api.scraperapi.com"


class ScraperAPIError(Exception):
    pass


def fetch_html(url: str, render: bool = False, timeout: int = 70) -> str:
    """Descarga el HTML de `url` a través de ScraperAPI.

    render=False por default: tanto Walmart como Farmacias del Ahorro
    resultaron traer el precio en el HTML inicial (sin necesitar ejecutar
    JavaScript) -- confirmamos que FDA lo tenía en una metaetiqueta simple,
    y activar el renderizado (render=true) causó errores 500 del propio
    servidor de ScraperAPI en la primera prueba, además de costar más
    créditos. Si algún sitio nuevo sí lo necesitara, se puede llamar con
    render=True explícitamente.
    """
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
    last_error = None
    for intento in range(2):  # 1 reintento por si el 500 fue transitorio
        resp = requests.get(API_BASE, params=params, timeout=timeout)
        if resp.status_code < 500:
            resp.raise_for_status()
            return resp.text
        last_error = resp
    last_error.raise_for_status()
    return last_error.text
