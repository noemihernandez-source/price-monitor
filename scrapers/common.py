"""
Utilidades compartidas entre scrapers.

Estrategia de extracción de precio:
1. Buscar datos estructurados JSON-LD (<script type="application/ld+json">) con
   schema.org/Product -> offers -> price.
2. Buscar metaetiquetas Open Graph / itemprop (<meta property="product:price:amount">),
   muy común en sitios VTEX y otros e-commerce.
3. Si nada de eso hay, caer a una lista de selectores CSS candidatos (fallback).
"""
import json
import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class PriceResult:
    price: Optional[float]
    currency: str
    in_stock: Optional[bool]
    method: str  # "json-ld", "meta-tag", "css-fallback", "api", o "not-found"
    raw_snippet: str = ""


def extract_price_from_jsonld(html: str) -> Optional[PriceResult]:
    """Busca schema.org/Product en bloques JSON-LD y devuelve el precio."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.text
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            sub_candidates = graph if isinstance(graph, list) else [item]
            for sub in sub_candidates:
                if not isinstance(sub, dict):
                    continue
                if sub.get("@type") not in ("Product", ["Product"]):
                    continue
                offers = sub.get("offers")
                if isinstance(offers, list):
                    offers = offers[0] if offers else None
                if not isinstance(offers, dict):
                    continue
                price = offers.get("price") or offers.get("lowPrice")
                if price is None:
                    continue
                try:
                    price_val = float(str(price).replace(",", ""))
                except ValueError:
                    continue
                availability = offers.get("availability", "")
                in_stock = "InStock" in availability if availability else None
                return PriceResult(
                    price=price_val,
                    currency=offers.get("priceCurrency", "MXN"),
                    in_stock=in_stock,
                    method="json-ld",
                )
    return None


PRICE_REGEX = re.compile(r"\$?\s?(\d{1,3}(?:[.,]\d{3})*(?:\.\d{2})?)")


def extract_price_from_meta_tags(html: str) -> Optional[PriceResult]:
    """Fallback #2: muchos sitios (incluyendo tiendas VTEX como Farmacias del
    Ahorro, y varios temas de e-commerce) ponen el precio en metaetiquetas
    Open Graph / itemprop en el <head>, aunque no tengan JSON-LD completo.
    Esto es más estable que adivinar clases CSS porque casi nadie las quita
    (las usan para que se vea bien al compartir el link en redes)."""
    soup = BeautifulSoup(html, "html.parser")
    meta_candidates = [
        {"property": "product:price:amount"},
        {"property": "og:price:amount"},
        {"itemprop": "price"},
        {"name": "price"},
    ]
    for attrs in meta_candidates:
        tag = soup.find("meta", attrs=attrs)
        if not tag:
            continue
        content = tag.get("content")
        if not content:
            continue
        try:
            price_val = float(str(content).replace(",", ""))
            return PriceResult(price=price_val, currency="MXN", in_stock=None, method="meta-tag")
        except ValueError:
            continue
    return None


def extract_price_from_selectors(html: str, selectors: list[str]) -> Optional[PriceResult]:
    """Fallback: prueba una lista de selectores CSS candidatos en orden."""
    soup = BeautifulSoup(html, "html.parser")
    for selector in selectors:
        el = soup.select_one(selector)
        if not el:
            continue
        text = el.get_text(strip=True)
        match = PRICE_REGEX.search(text)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                return PriceResult(
                    price=float(price_str),
                    currency="MXN",
                    in_stock=None,
                    method="css-fallback",
                    raw_snippet=text[:80],
                )
            except ValueError:
                continue
    return None


async def fetch_rendered_html(url: str, wait_selector: str = "body", timeout_ms: int = 20000) -> str:
    """Carga una página con Playwright (headless) y devuelve el HTML ya renderizado.
    Necesario para sitios SPA (Walmart MX, muchos VTEX) donde el precio se
    inyecta con JavaScript y no aparece en el HTML crudo."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        try:
            await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            try:
                await page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except Exception:
                pass  # seguimos con lo que haya cargado
            html = await page.content()
        finally:
            await browser.close()
        return html
