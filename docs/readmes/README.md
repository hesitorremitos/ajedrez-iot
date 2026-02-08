# Async and Events Guide (ESP32 + MicroPython)

Esta carpeta explica, de forma progresiva, el modelo de ejecucion que estamos usando
para boton de turno, reloj, SSE y render.

## Orden recomendado

1. `01-async-basics.md`
2. `02-interrupts-flags-and-schedule.md`
3. `03-event-queue-architecture.md`

## Objetivo

- Entender por que usamos `while True` con `await`.
- Entender cuando usar callbacks de IRQ y cuando no.
- Entender `ThreadSafeFlag`, `Queue`, `micropython.schedule()`.
- Tener patrones listos para codigo simple y robusto.

## Regla de oro

En IRQ (interrupcion) solo marcar una senal rapida.
Toda logica pesada (reloj, historial, render, SSE, JSON) va fuera de IRQ en tareas async.
