from microdot import Microdot, Response
from microdot_websocket import with_websocket
from modules.network import AccessPoint
import time
import ujson as json
ap = AccessPoint("RED GRATIS")
ap.start()
app = Microdot()
STATE = {
    "bootTime": time.time(),
    "messages": 0,
    "lastMessage": "",
}

HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Zulma WS Test</title>
  <style>
    body { font-family: sans-serif; margin: 24px; max-width: 760px; }
    h1 { margin: 0 0 12px; }
    .row { display: flex; gap: 8px; margin-bottom: 12px; }
    input, button { padding: 10px; }
    input { flex: 1; }
    pre { background: #111; color: #ddd; padding: 12px; border-radius: 8px; min-height: 180px; }
    .ok { color: #0a7b34; }
    .bad { color: #b42318; }
  </style>
</head>
<body>
  <h1>Microdot + WebSocket</h1>
  <p>Prueba rapida para validar <code>microdot.py</code> y <code>microdot-websocket.py</code>.</p>
  <p>Estado: <strong id="status" class="bad">desconectado</strong></p>
  <div class="row">
    <input id="msg" placeholder="Escribe un mensaje" value="hola tablero">
    <button id="send">Enviar</button>
  </div>
  <pre id="log"></pre>

  <script>
    const log = document.getElementById('log');
    const statusEl = document.getElementById('status');
    const msgEl = document.getElementById('msg');
    const sendBtn = document.getElementById('send');

    const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${scheme}://${location.host}/ws`);

    function write(line) {
      log.textContent += line + '\\n';
      log.scrollTop = log.scrollHeight;
    }

    ws.onopen = () => {
      statusEl.textContent = 'conectado';
      statusEl.className = 'ok';
      write('[open] websocket conectado');
    };

    ws.onmessage = (event) => write('[recv] ' + event.data);

    ws.onclose = () => {
      statusEl.textContent = 'cerrado';
      statusEl.className = 'bad';
      write('[close] websocket cerrado');
    };

    ws.onerror = () => write('[error] fallo websocket');

    sendBtn.onclick = () => {
      const payload = msgEl.value || 'ping';
      ws.send(payload);
      write('[send] ' + payload);
    };
  </script>
</body>
</html>
"""


@app.get("/")
def index(request):
    return Response(HTML, headers={"Content-Type": "text/html; charset=UTF-8"})


@app.get("/api/state")
def getState(request):
    uptime = int(time.time() - STATE["bootTime"])
    return {
        "uptime": uptime,
        "messages": STATE["messages"],
        "lastMessage": STATE["lastMessage"],
    }


@app.route("/ws")
@with_websocket
async def wsHandler(request, ws):
    await ws.send(json.dumps({"type": "hello", "ok": True}))
    while True:
        message = await ws.receive()
        STATE["messages"] += 1
        STATE["lastMessage"] = message
        await ws.send(
            json.dumps(
                {
                    "type": "echo",
                    "message": message,
                    "count": STATE["messages"],
                }
            )
        )


def main():
    app.run(host="0.0.0.0", port=80, debug=True)


if __name__ == "__main__":
    main()

