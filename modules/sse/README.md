# SSE Module

Modulo SSE minimo para MicroPython en ESP32.

Envia solo el ultimo mensaje disponible a los clientes conectados al stream.

## Uso

```python
import ujson as json
from microdot import Microdot, Response
from modules.sse import SSE

app = Microdot()
sse = SSE()

@app.get('/events')
def events(request):
    return Response(
        sse.stream(),
        headers={'Content-Type': 'text/event-stream'}
    )

@app.post('/move')
async def move(request):
    data = request.json or {}
    await sse.send(json.dumps({'move': data.get('move', '')}))
    return {'ok': True}
```

## Nota

- No implementa cola persistente ni confirmaciones tipo MQTT.
- Mantiene solo el ultimo mensaje en memoria (`_buffer`).
- Si llegan varios updates muy rapido, se conserva el ultimo.

## Reconexion y coherencia

Para mantener el historial consistente en cliente:

- Incluye un `id` incremental por movimiento en cada evento SSE.
- Si el cliente detecta saltos (`id` esperado != `id` recibido), consulta
  `GET /api/history` para recuperar movimientos faltantes.
- Mantiene el stream SSE liviano y delega recuperacion puntual al endpoint de historial.
