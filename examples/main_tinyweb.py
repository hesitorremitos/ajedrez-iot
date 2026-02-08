import gc
import time
import uasyncio as asyncio
import ujson as json

import tinyweb

try:
    from machine import Pin
except ImportError:
    Pin = None

from modules.network import AccessPoint
from modules.sse import SSE


ap = AccessPoint("RED GRATIS")
ap.start()

app = tinyweb.webserver(max_concurrency=10, backlog=8, debug=False)
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
  <title>Zulma SSE Test (Tinyweb)</title>
  <link rel="stylesheet" href="/assets/app.css">
</head>
<body>
  <h1>SSE board updates (Tinyweb)</h1>
  <p>RAM libre: <strong id="mem">-</strong></p>
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
const moveInput = document.getElementById('moveInput');

const fmtMem = (bytes) => {
  if (typeof bytes !== 'number') return '-';
  return `${bytes} bytes (~${(bytes / 1024).toFixed(1)} KiB)`;
};

const write = (line) => {
  log.textContent += line + '\\n';
  log.scrollTop = log.scrollHeight;
};

const showMem = (value) => {
  mem.textContent = fmtMem(value);
};

const es = new EventSource('/events');
es.onopen = () => write('[open] SSE conectado');
es.onerror = () => write('[error] SSE reconectando...');

es.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  showMem(msg.mem_free);
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
  showMem(data.mem_free);
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


async def send_text(resp, content_type, body, status=200):
    resp.code = status
    resp.add_header("Content-Type", content_type)
    resp.add_header("Content-Length", str(len(body)))
    await resp._send_headers()
    await resp.send(body)


async def send_json(resp, payload, status=200):
    body = json.dumps(payload)
    await send_text(resp, "application/json", body, status=status)


@app.route("/")
async def index(req, resp):
    await send_text(resp, "text/html; charset=UTF-8", HTML)


@app.route("/assets/<name>")
async def assets(req, resp, name):
    if name == "app.css":
        await send_text(resp, "text/css", CSS)
    elif name == "app.js":
        await send_text(resp, "application/javascript", JS)
    else:
        await send_text(resp, "text/plain", "Not found", status=404)


@app.route("/api/state")
async def state(req, resp):
    await send_json(resp, get_state())


@app.route("/api/history")
async def history(req, resp):
    await send_json(resp, {"history": HISTORY})


@app.route("/move", methods=["POST"], save_headers=["Content-Length", "Content-Type"])
async def move(req, resp):
    global LAST_MOVE, STATE_VERSION
    data = await req.read_parse_form_data()
    if not data:
        data = {}

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
    await send_json(resp, payload)


@app.route("/events")
async def events(req, resp):
    resp.version = "1.1"
    resp.code = 200
    resp.add_header("Content-Type", "text/event-stream")
    resp.add_header("Cache-Control", "no-cache")
    resp.add_header("Connection", "keep-alive")
    await resp._send_headers()
    async for chunk in sse.stream():
        await resp.send(chunk)


print("Tinyweb SSE demo iniciado. mem_free:", mem_free())
app.loop.create_task(blink_led_task())
app.run(host="0.0.0.0", port=80)
