# Interrupciones, Flags y `micropython.schedule()`

## 1) Contexto: IRQ no es contexto normal

Cuando un pin dispara IRQ, el handler corre en contexto restringido.

En IRQ evita:

- `await`
- JSON
- I/O pesada
- operaciones largas
- crear muchos objetos

Haz solo esto:

- marcar un flag
- guardar un timestamp simple

## 2) `ThreadSafeFlag` (recomendado con uasyncio)

Patron minimo:

```python
import uasyncio as asyncio
from machine import Pin
import time

flag = asyncio.ThreadSafeFlag()
last_ms = 0

def irq_handler(pin):
    flag.set()  # rapido y seguro

button = Pin(0, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=irq_handler)

async def button_worker():
    global last_ms
    while True:
        await flag.wait()
        now = time.ticks_ms()
        if time.ticks_diff(now, last_ms) < 150:  # debounce
            continue
        last_ms = now
        # logica real aqui (fuera de IRQ)
        print("turn pressed")
```

Ventajas:

- IRQ ultra corta.
- Cero trabajo pesado en interrupcion.
- Flujo claro y legible.

## 3) `micropython.schedule()`

`micropython.schedule(func, arg)` agenda una funcion para correr pronto en contexto normal.

Ejemplo:

```python
import micropython
from machine import Pin

pending = 0

def scheduled_cb(_):
    global pending
    pending += 1

def irq_handler(pin):
    micropython.schedule(scheduled_cb, 0)

Pin(0, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=irq_handler)
```

Notas:

- Es util si no usas `uasyncio`.
- En app async, normalmente `ThreadSafeFlag` + worker es mas directo.

## 4) Diferencia practica: `ThreadSafeFlag` vs `schedule`

- `ThreadSafeFlag`:
  - integra mejor con `uasyncio`
  - facil de encadenar con `Queue`
- `schedule`:
  - bueno para salir rapido de IRQ
  - requiere coordinar despues con tu propio estado/cola

## 5) Debounce correcto

Haz debounce fuera de IRQ:

```python
if time.ticks_diff(now, last_ms) < 150:
    continue
```

No hagas delays dentro de IRQ.

## 6) Ejemplo intermedio: IRQ -> flag -> cola

```python
import uasyncio as asyncio

flag = asyncio.ThreadSafeFlag()
events = asyncio.Queue(16)

def irq_handler(pin):
    flag.set()

async def irq_bridge():
    while True:
        await flag.wait()
        await events.put(("turn_pressed", 0))

async def coordinator():
    while True:
        evt, _ = await events.get()
        if evt == "turn_pressed":
            # reloj, render, SSE, historial
            pass
```

Este es el patron mas usado en firmware reactivo para ESP32.
