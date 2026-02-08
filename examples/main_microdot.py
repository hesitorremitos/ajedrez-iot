import asyncio
import gc
import time
import ujson as json

from microdot import Microdot, Response
from modules.network import AccessPoint
from modules.sse import SSE

try:
    from machine import Pin
except ImportError:
    Pin = None


ap = AccessPoint("RED GRATIS")
ap.start()

app = Microdot()
sse = SSE()

LAST_MOVE = ""
STATE_VERSION = 0
HISTORY_LIMIT = 100
HISTORY = []
mem_free = getattr(gc, "mem_free", lambda: 0)
ticks_ms = getattr(time, "ticks_ms", lambda: 0)

LED_PIN = 2
LED_BLINKS = 0

if Pin is not None:
    try:
        _led = Pin(LED_PIN, Pin.OUT)
    except Exception:
        _led = None
else:
    _led = None


HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Zulma SSE Test (Microdot)</title>
  <link rel="stylesheet" href="/assets/app.css">
</head>
<body>
  <h1>SSE board updates (Microdot)</h1>
  <p>RAM libre: <strong id="mem">-</strong></p>
  <p>Blinks LED: <strong id="blinks">0</strong></p>
  <p>Conectado a <code>/events</code>. Envia cualquier movimiento sin validacion.</p>
  <input id="moveInput" placeholder="Ej: e2e4" value="e2e4" />
  <button id="btnMove">Enviar movimiento</button>
  <button id="btnState">Ver estado actual</button>
  <pre id="log"></pre>
  <script src="/assets/app.js"></script>
</body>
</html>
"""

CSS = """body { font-family: sans-serif; margin: 20px; }
button { padding: 10px 14px; margin-right: 8px; }
pre { background: #111; color: #ddd; padding: 12px; border-radius: 8px; min-height: 180px; }
"""

JS = """const log = document.getElementById('log');
const mem = document.getElementById('mem');
const blinks = document.getElementById('blinks');
const moveInput = document.getElementById('moveInput');

const fmtMem = (bytes) => {
  if (typeof bytes !== 'number') return '-';
  return `${bytes} bytes (~${(bytes / 1024).toFixed(1)} KiB)`;
};

const write = (line) => {
  log.textContent += line + '\\n';
  log.scrollTop = log.scrollHeight;
};

const showState = (data) => {
  mem.textContent = fmtMem(data.mem_free);
  blinks.textContent = String(data.led_blinks || 0);
};

const es = new EventSource('/events');
es.onopen = () => write('[open] SSE conectado');
es.onerror = () => write('[error] SSE reconectando...');
es.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  showState(msg);
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
  showState(data);
  write('[state] ' + JSON.stringify(data));
};
"""


def get_state():
    return {
        "move": LAST_MOVE,
        "version": STATE_VERSION,
        "mem_free": mem_free(),
        "led_blinks": LED_BLINKS,
        "uptime_ms": ticks_ms(),
    }


async def blink_led_task(period_ms=500):
    global LED_BLINKS
    if _led is None:
        while True:
            await asyncio.sleep_ms(period_ms)
    while True:
        _led.value(0 if _led.value() else 1)
        LED_BLINKS += 1
        await asyncio.sleep_ms(period_ms)


@app.get("/")
def index(request):
    return Response(HTML, headers={"Content-Type": "text/html; charset=UTF-8"})


@app.get("/assets/<path:filename>")
def assets(request, filename):
    if filename == "app.css":
        return Response(CSS, headers={"Content-Type": "text/css"})
    if filename == "app.js":
        return Response(JS, headers={"Content-Type": "application/javascript"})
    return Response("Not found", status_code=404)


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
    try:
        await sse.send(json.dumps(payload), event_id=STATE_VERSION)
    except TypeError:
        await sse.send(json.dumps(payload))
    return payload


@app.get("/events")
def events(request):
    return Response(
        sse.stream(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
        },
    )


async def main():
    asyncio.create_task(blink_led_task())
    await app.start_server(host="0.0.0.0", port=80, debug=True)


print("Microdot SSE demo iniciado. mem_free:", mem_free())
asyncio.run(main())
