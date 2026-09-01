"""
Orquestador diario de monitoreo de precios.

Qué hace:
1. Lee config/products.csv (su catálogo).
2. Para cada producto, consulta el precio en Walmart, Farmacias del Ahorro
   y Mercado Libre.
3. Compara cada precio contra su precio de Amazon.
4. Guarda:
   - data/history.csv  -> un renglón por producto/tienda/día (para ver tendencia)
   - data/latest.json  -> snapshot del día de hoy (lo usa el dashboard)
   - data/dashboard_data.js -> mismo contenido que latest.json pero como
     variable JS, para que dashboard.html lo pueda abrir directo con
     doble-click sin necesitar un servidor (evita problemas de CORS con
     file://).

Uso:
    python main.py

Automatización (ver README.md para más detalle):
    - Local: cron / Task Scheduler corriendo `python main.py` una vez al día.
    - Recomendado: GitHub Actions con este mismo repo, corre gratis y además
      deja el dashboard publicado solo si usan GitHub Pages.
"""
import asyncio
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from scrapers import farmacias_ahorro, mercadolibre, walmart

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "products.csv"
DATA_DIR = BASE_DIR / "data"
HISTORY_PATH = DATA_DIR / "history.csv"
LATEST_JSON_PATH = DATA_DIR / "latest.json"
DASHBOARD_JS_PATH = BASE_DIR / "dashboard_data.js"


async def check_product(row: dict) -> dict:
    sku = row["sku"]
    nombre = row["nombre"]
    precio_amazon = float(row["precio_amazon"])
    # CRÍTICO: no todas las tiendas venden el mismo tamaño de paquete del
    # mismo producto (ej. Farmacias del Ahorro vende la barra suelta,
    # Amazon/Walmart la venden en pack de 5). Comparar precio de paquete
    # contra precio de paquete de tamaño distinto genera falsas alarmas.
    # Por eso TODO se normaliza a precio-por-unidad antes de comparar.
    # unidades_amazon/unidades_walmart/unidades_fda/unidades_ml deben venir
    # en el config CSV (cuántas barras/piezas trae el paquete en cada tienda).
    unidades_amazon = int(row.get("unidades_amazon", 1) or 1)
    precio_amazon_unidad = precio_amazon / unidades_amazon

    walmart_result = await walmart.get_price(row["url_walmart"])
    fda_result = await farmacias_ahorro.get_price(row["url_farmacias_ahorro"])
    # La llamada a Mercado Libre es sync (usa requests), la corremos en un
    # thread para no bloquear el loop de asyncio mientras esperan las otras.
    ml_result = await asyncio.to_thread(mercadolibre.get_price, row["mercadolibre_query"])

    tiendas = {
        "Walmart": (walmart_result, int(row.get("unidades_walmart", 1) or 1)),
        "Farmacias del Ahorro": (fda_result, int(row.get("unidades_fda", 1) or 1)),
        "Mercado Libre": (ml_result, int(row.get("unidades_ml", 1) or 1)),
    }

    precios = {}
    for tienda, (resultado, unidades) in tiendas.items():
        precio = resultado.price
        precio_unidad = round(precio / unidades, 2) if precio is not None else None
        por_debajo_de_amazon = (precio_unidad is not None) and (precio_unidad < precio_amazon_unidad)
        precios[tienda] = {
            "precio": precio,
            "unidades": unidades,
            "precio_por_unidad": precio_unidad,
            "metodo": resultado.method,
            "por_debajo_de_amazon": por_debajo_de_amazon,
            "diferencia": round(precio_amazon_unidad - precio_unidad, 2) if precio_unidad is not None else None,
        }

    return {
        "sku": sku,
        "nombre": nombre,
        "precio_amazon": precio_amazon,
        "tiendas": precios,
    }


async def run() -> list[dict]:
    with open(CONFIG_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    resultados = []
    for row in rows:
        print(f"Revisando: {row['nombre']} ({row['sku']})...")
        try:
            resultado = await check_product(row)
        except Exception as exc:  # no queremos que un producto tumbe todo el corrido
            print(f"  ERROR en {row['sku']}: {exc}")
            resultado = {
                "sku": row["sku"],
                "nombre": row["nombre"],
                "precio_amazon": float(row["precio_amazon"]),
                "tiendas": {},
                "error": str(exc),
            }
        resultados.append(resultado)
    return resultados


def save_results(resultados: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Snapshot de hoy (lo consume el dashboard)
    snapshot = {"generado": timestamp, "productos": resultados}
    LATEST_JSON_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Mismo contenido como variable JS, para abrir el dashboard sin servidor
    js_content = "window.PRICE_DATA = " + json.dumps(snapshot, ensure_ascii=False) + ";"
    DASHBOARD_JS_PATH.write_text(js_content, encoding="utf-8")

    # 3. Histórico acumulado (para ver tendencias en el tiempo)
    is_new_file = not HISTORY_PATH.exists()
    with open(HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["fecha", "sku", "nombre", "tienda", "precio", "precio_amazon", "por_debajo_de_amazon"])
        for producto in resultados:
            for tienda, info in producto.get("tiendas", {}).items():
                writer.writerow([
                    timestamp,
                    producto["sku"],
                    producto["nombre"],
                    tienda,
                    info["precio"],
                    producto["precio_amazon"],
                    info["por_debajo_de_amazon"],
                ])

    alertas = [
        (p["nombre"], t, i["precio"], p["precio_amazon"])
        for p in resultados
        for t, i in p.get("tiendas", {}).items()
        if i["por_debajo_de_amazon"]
    ]
    print(f"\nListo. {len(resultados)} productos revisados.")
    if alertas:
        print(f"\n⚠️  {len(alertas)} alerta(s) de precio por debajo de Amazon:")
        for nombre, tienda, precio, precio_amazon in alertas:
            print(f"  - {nombre} en {tienda}: ${precio} (Amazon: ${precio_amazon})")
    else:
        print("Sin alertas: ninguna tienda está por debajo del precio de Amazon.")


if __name__ == "__main__":
    resultados = asyncio.run(run())
    save_results(resultados)
