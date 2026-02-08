import gc
import uasyncio as asyncio
import ujson as json
import time

try:
    from machine import Pin
except ImportError:
    Pin = None

from nanoweb import Nanoweb
from modules.network import AccessPoint
from modules.sse import SSE


ap = AccessPoint("RED GRATIS")
ap.start()

app = Nanoweb(port=80, address="0.0.0.0")
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
  <title>Zulma SSE Test (Nanoweb)</title>
  <link rel="stylesheet" href="/assets/app.css">
</head>
<body>
  <h1>SSE board updates (Nanoweb)</h1>
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


async def write_data(request, data):
    if isinstance(data, str):
        data = data.encode()
    await request.write(data)


async def write_response(request, status, content_type, body):
    if isinstance(body, str):
        body = body.encode()
    await write_data(request, "HTTP/1.1 %d OK\r\n" % status)
    await write_data(request, "Content-Type: %s\r\n" % content_type)
    await write_data(request, "Content-Length: %d\r\n\r\n" % len(body))
    await write_data(request, body)


async def write_json(request, payload):
    await write_response(request, 200, "application/json", json.dumps(payload))


@app.route("/")
async def index(request):
    await write_response(request, 200, "text/html; charset=UTF-8", HTML)


@app.route("/assets/*")
async def assets(request):
    path = request.url
    if path.endswith("/app.css"):
        await write_response(request, 200, "text/css", CSS)
    elif path.endswith("/app.js"):
        await write_response(request, 200, "application/javascript", JS)
    else:
        await write_response(request, 404, "text/plain", "Not found")


@app.route("/api/state")
async def state(request):
    await write_json(request, get_state())


@app.route("/api/history")
async def history(request):
    await write_json(request, {"history": HISTORY})


@app.route("/move")
async def move(request):
    global LAST_MOVE, STATE_VERSION
    if request.method != "POST":
        await write_response(request, 405, "text/plain", "Method Not Allowed")
        return

    size = int(request.headers.get("Content-Length", "0"))
    raw = await request.read(size) if size > 0 else b"{}"
    try:
        data = json.loads(raw.decode())
    except Exception:
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
    await write_json(request, payload)


@app.route("/events")
async def events(request):
    await write_data(request, "HTTP/1.1 200 OK\r\n")
    await write_data(request, "Content-Type: text/event-stream\r\n")
    await write_data(request, "Cache-Control: no-cache\r\n")
    await write_data(request, "Connection: keep-alive\r\n\r\n")
    async for chunk in sse.stream():
        await write_data(request, chunk)


print("Nanoweb SSE demo iniciado. mem_free:", mem_free())
loop = asyncio.get_event_loop()
loop.create_task(blink_led_task())
loop.create_task(app.run())
loop.run_forever()
