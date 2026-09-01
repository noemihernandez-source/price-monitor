# Monitor de precios: Amazon vs. Walmart / Farmacias del Ahorro / Mercado Libre

Revisa diario si alguna tienda tiene un precio más bajo que Amazon, para
evitar la penalización de Amazon por política de precio más bajo del
mercado.

## Qué incluye

- `scrapers/walmart.py` y `scrapers/farmacias_ahorro.py` — obtienen el precio
  renderizando la página con Playwright y leyendo datos estructurados
  (JSON-LD), con selectores CSS de respaldo.
- `scrapers/mercadolibre.py` — usa la **API pública oficial** de Mercado
  Libre (no es scraping, es más confiable).
- `main.py` — orquestador: corre los 3 scrapers para todo el catálogo,
  compara contra el precio de Amazon y guarda los resultados.
- `dashboard.html` — dashboard visual, se abre directo en el navegador
  (doble clic), no necesita servidor.
- `.github/workflows/monitoreo-diario.yml` — automatización gratuita con
  GitHub Actions (corre todos los días a las 7am hora CDMX).

## ⚠️ Antes de usarlo en producción: calibración inicial

Este código fue escrito sin poder probarlo en vivo contra walmart.com.mx ni
farmaciasdelahorro.com.mx (no tuve acceso de red a esos sitios desde donde
lo construí). La lógica es sólida y usa el método más estable que existe
(JSON-LD, que la mayoría de tiendas grandes usa para aparecer en Google
Shopping), pero **hay que validarlo con productos reales antes de confiar en
los resultados**:

1. Reemplacen las URLs de ejemplo en `config/products.csv` por productos
   reales de su catálogo.
2. Corran un producto a la vez para revisar que sí esté agarrando el precio
   correcto:
   ```bash
   python -m scrapers.walmart "https://www.walmart.com.mx/ip/producto-real/12345"
   python -m scrapers.farmacias_ahorro "https://www.farmaciasdelahorro.com.mx/producto-real/p"
   python -m scrapers.mercadolibre "https://articulo.mercadolibre.com.mx/MLM-123456789-producto-real"
   ```
3. Si el método que imprime es `not-found`, el sitio no trajo JSON-LD en esa
   página — hay que inspeccionar el HTML real (clic derecho → Inspeccionar
   sobre el precio) y agregar el selector correcto a `FALLBACK_SELECTORS` en
   el scraper correspondiente.

## Instalación

```bash
python -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps chromium
```

## Uso manual

1. Editen `config/products.csv` con sus 18-30 SKUs reales: nombre, precio de
   Amazon, y la URL (o búsqueda) en cada tienda.
2. Corran:
   ```bash
   python main.py
   ```
3. Abran `dashboard.html` en el navegador para ver los resultados.

Cada corrida genera:
- `data/latest.json` — snapshot del día.
- `data/history.csv` — histórico acumulado (útil para ver tendencia de
  precios en el tiempo, no solo el estado actual).
- `dashboard_data.js` — lo que lee el dashboard.

## Automatizarlo (para que corra solo, sin intervención manual)

**Opción recomendada — GitHub Actions (gratis):**
1. Suban esta carpeta a un repositorio de GitHub (puede ser privado).
2. El workflow en `.github/workflows/monitoreo-diario.yml` ya está
   configurado para correr todos los días a las 7am hora CDMX.
3. Para ver el dashboard actualizado sin descargar nada, activen GitHub
   Pages apuntando a la rama principal — así `dashboard.html` queda
   accesible en una URL pública (o pueden dejarlo privado si el repo lo es).
4. También pueden correrlo manualmente cuando quieran desde la pestaña
   "Actions" del repo, sin esperar al cron.

**Alternativa — cron local / servidor propio:**
Si prefieren correrlo en su propia infraestructura, agreguen una línea de
cron:
```
0 7 * * * cd /ruta/al/proyecto && venv/bin/python main.py
```

## Alertas (siguiente paso opcional)

Ahora mismo `main.py` imprime las alertas en consola. Si quieren que les
llegue un email o mensaje de Slack cuando algo esté por debajo de Amazon, se
puede agregar fácilmente al final de `save_results()` en `main.py` — avísenme
y lo agrego (necesito saber si prefieren email, Slack, o WhatsApp).

## Consideraciones importantes

- **Términos de servicio:** varios sitios prohíben el scraping automatizado
  en sus términos. El riesgo práctico más común es que la IP se bloquee
  temporalmente si se hacen demasiadas solicitudes muy seguido — con 18-30
  SKUs una vez al día el riesgo es bajo, pero no es cero.
- **Mantenimiento:** cuando Walmart o Farmacias del Ahorro rediseñen su
  sitio (pasa un par de veces al año), el scraper de esa tienda puede dejar
  de encontrar el precio. El aviso será claro: en el dashboard esa celda
  dirá "Sin dato" en vez de mostrar un precio viejo o incorrecto.
- **Farmacias Guadalajara, Chedraui y GNC** no están incluidas en esta
  primera versión (acordamos empezar con las 3 originales). La misma
  estructura de `scrapers/` sirve para agregarlas después — cada una es un
  archivo nuevo siguiendo el mismo patrón.
