# Async Basico en MicroPython

## 1) Que es `uasyncio`

`uasyncio` es un loop cooperativo: varias tareas comparten CPU en un solo hilo.

- No hay paralelismo real por nucleo como en hilos del sistema operativo.
- Cada tarea cede control con `await`.
- Si una tarea nunca hace `await`, bloquea a las demas.

## 2) `while True` no siempre significa "gastar CPU"

Este patron es correcto:

```python
import uasyncio as asyncio

async def worker():
    while True:
        await asyncio.sleep_ms(1000)
        print("tick")
```

Por que no quema CPU:

- `await asyncio.sleep_ms(...)` duerme la tarea.
- El loop ejecuta otras tareas o queda en espera.

Este patron si bloquea:

```python
async def bad_worker():
    while True:
        pass
```

## 3) Crear tareas concurrentes

```python
import uasyncio as asyncio

async def a():
    while True:
        print("A")
        await asyncio.sleep_ms(500)

async def b():
    while True:
        print("B")
        await asyncio.sleep_ms(700)

async def main():
    asyncio.create_task(a())
    asyncio.create_task(b())
    while True:
        await asyncio.sleep_ms(1000)

asyncio.run(main())
```

## 4) Confiabilidad: "funciona siempre bien?"

Si sigues estas reglas, es muy estable:

1. Tareas cortas, con `await` frecuentes.
2. Nada pesado dentro de IRQ.
3. Evitar allocs grandes en bucles calientes.
4. Manejar excepciones en workers para que no mueran silenciosamente.
5. Limitar concurrencia de red en ESP32.

## 5) Patrón recomendado para servidor + tareas

```python
async def main():
    asyncio.create_task(blink_led())
    asyncio.create_task(button_worker())
    await start_http_server()
```

- `start_http_server()` mantiene la app viva.
- Las otras tareas corren en paralelo cooperativo.

## 6) Errores comunes

- Bloquear con `time.sleep()` en vez de `await asyncio.sleep_ms()`.
- Hacer JSON/render/SSE dentro de IRQ.
- Creer que `while True` siempre es malo (no lo es si hay `await`).
