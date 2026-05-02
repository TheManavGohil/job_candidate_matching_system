"""
Plugin SDK endpoints – widget.js and embedded UI.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

router = APIRouter(prefix="/api/v1/sdk", tags=["sdk"])


WIDGET_JS_TEMPLATE = """
(function() {
  var script = document.currentScript;
  var apiKey = script.getAttribute('data-company-api-key') || '';
  var container = document.getElementById('match-widget');
  if (!container) {
    container = document.createElement('div');
    container.id = 'match-widget';
    script.parentNode.insertBefore(container, script.nextSibling);
  }

  var iframe = document.createElement('iframe');
  iframe.src = '%BASE_URL%/api/v1/sdk/ui?api_key=' + encodeURIComponent(apiKey);
  iframe.style.width = '100%%';
  iframe.style.height = '700px';
  iframe.style.border = 'none';
  iframe.style.borderRadius = '12px';
  iframe.style.boxShadow = '0 4px 24px rgba(0,0,0,0.12)';
  iframe.allow = 'clipboard-write';

  container.appendChild(iframe);
})();
"""


@router.get("/widget.js")
async def get_widget_js(request: Request):
    """Return the embeddable JavaScript snippet."""
    base_url = str(request.base_url).rstrip("/")
    js = WIDGET_JS_TEMPLATE.replace("%BASE_URL%", base_url)
    return Response(content=js, media_type="application/javascript")


@router.get("/ui", response_class=HTMLResponse)
async def get_embedded_ui(api_key: str = ""):
    """Redirect / proxy to the frontend in embedded mode."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Matching Engine Widget</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            iframe {{ width: 100%; height: 100vh; border: none; }}
        </style>
    </head>
    <body>
        <iframe src="http://localhost:3000?embedded=true&api_key={api_key}"></iframe>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
