"""
Prueba GRATIS antes de pagar ScraperAPI: intenta traer la página de Walmart
con una petición HTTP simple (requests), sin Playwright y sin ningún
servicio de terceros. Si esto funciona, no necesitamos gastar en nada.
"""
import sys

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}


def debug(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    print(f"Status code: {resp.status_code}")
    print(f"Tamaño de la respuesta: {len(resp.text)} caracteres")

    with open("debug_output_simple.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

    print("\n--- PRIMEROS 1000 CARACTERES ---")
    print(resp.text[:1000])
    print("--- FIN DEL EXTRACTO ---\n")

    señales_bloqueo = ["cf-mitigated", "cf_chl_", "Just a moment", "Checking your browser", "Access Denied"]
    encontradas = [s for s in señales_bloqueo if s.lower() in resp.text.lower()]
    if encontradas:
        print(f"⚠️  Señales de bloqueo detectadas: {encontradas}")
    else:
        print("✅ No se detectaron señales típicas de bloqueo Cloudflare en el texto.")


if __name__ == "__main__":
    debug(sys.argv[1])
