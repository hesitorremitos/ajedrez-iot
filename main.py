import gc
import ujson as json

from microdot import Microdot, Response
from modules.network import AccessPoint
from modules.sse import SSE


ap = AccessPoint("RED GRATIS")
ap.start()

app = Microdot()
sse = SSE()

LAST_MOVE = ""
STATE_VERSION = 0
HISTORY_LIMIT = 100
HISTORY = []
mem_free = getattr(gc, "mem_free", lambda: 0)


def get_state():
    return {
        "move": LAST_MOVE,
        "mem_free": mem_free(),
    }


HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Zulma SSE Test</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    button { padding: 10px 14px; margin-right: 8px; }
    pre { background: #111; color: #ddd; padding: 12px; border-radius: 8px; min-height: 180px; }
  </style>
</head>
<body>
  <h1>SSE board updates</h1>
  <p>Conectado a <code>/events</code>. Envia cualquier movimiento sin validacion.</p>
  <input id="moveInput" placeholder="Ej: e2e4" value="e2e4" />
  <button id="btnMove">Enviar movimiento</button>
  <button id="btnState">Ver estado actual</button>
  <pre id="log"></pre>

  <script>
    const log = document.getElementById('log');
    const moveInput = document.getElementById('moveInput');
    const write = (line) => {
      log.textContent += line + '\\n';
      log.scrollTop = log.scrollHeight;
    };

    const es = new EventSource('/events');
    es.onopen = () => write('[open] SSE conectado');
    es.onerror = () => write('[error] SSE reconectando...');

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      write('[board] ' + JSON.stringify(msg));
    };

    document.getElementById('btnMove').onclick = async () => {
      const move = moveInput.value || '';
      await fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ move })
      });
      write('[send] move ' + move);
    };

    document.getElementById('btnState').onclick = async () => {
      const res = await fetch('/api/state');
      const data = await res.json();
      write('[state] ' + JSON.stringify(data));
    };
  </script>
</body>
</html>
"""


@app.get("/")
def index(request):
    return Response(HTML, headers={"Content-Type": "text/html; charset=UTF-8"})


@app.get("/api/state")
def state(request):
    return get_state()


@app.get("/api/history")
def history(request):
    return {"history": HISTORY}


@app.post("/move")
async def move(request):
    global LAST_MOVE, STATE_VERSION
    data = request.json or {}
    if "move" in data:
        LAST_MOVE = data["move"]
    STATE_VERSION += 1
    HISTORY.append(LAST_MOVE)
    if len(HISTORY) > HISTORY_LIMIT:
        HISTORY.pop(0)

    payload = get_state()
    await sse.send(json.dumps(payload))
    return payload


@app.get("/events")
def events(request):
    return Response(
        sse.stream(),
        headers={"Content-Type": "text/event-stream"},
    )


app.run(host="0.0.0.0", port=80, debug=True)
