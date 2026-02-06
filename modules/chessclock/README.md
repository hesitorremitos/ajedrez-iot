# Modulo ChessClock para ESP32 (MicroPython)

Contador regresivo lazy para ajedrez. Cada instancia representa un solo reloj (una instancia por jugador). Un coordinador externo crea 2 instancias y decide cual corre.

## Caracteristicas

- Contador regresivo lazy (sin threads ni timers)
- API minima: start, pause, resume, reset
- Ajuste de tiempo absoluto y relativo
- Consulta en ms, segundos o formato `MM:SS`
- Callback para timeout
- Optimizado para ESP32

## Instalacion

```python
from modules.chessclock import ChessClock
```

## API Publica

### Constructor

```python
clock = ChessClock(debug=False)
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `debug` | `bool` | Activa modo debug para mensajes de diagnostico. Default: `False` |

### Metodos de Control

#### `start(initial=None) -> True`

Inicia el reloj (lo deja corriendo). Setea `time=initial` y arranca.

```python
clock = ChessClock()
clock.start(300000)  # 5 minutos, arranca inmediatamente
clock.start()        # Usa initial guardado o default 5 min
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `initial` | `int` | Tiempo base en ms. Si no se provee, usa el guardado o default `300000` (5 min) |

#### `pause() -> True`

Pausa el reloj. Si estaba corriendo, sincroniza el descuento hasta ahora. Si ya estaba pausado, es no-op.

```python
clock.pause()
```

#### `resume() -> True`

Reanuda el reloj desde el tiempo actual. Si `time` es 0, no vuelve a correr (no-op). Si ya estaba corriendo, es no-op.

```python
clock.resume()
```

### Configuracion / Reset

#### `reset(initial=None) -> True`

Deja el reloj pausado con `time=initial`. Limpia el latch de timeout.

```python
clock.reset(600000)  # Reset a 10 minutos, pausado
clock.reset()        # Reset con initial guardado o default
```

### Ajustes de Tiempo

#### `setTime(ms) -> True`

Fija el tiempo restante actual. Si el reloj esta corriendo, sincroniza primero y continua. Si el resultado es 0, entra en timeout.

```python
clock.setTime(120000)  # Fijar a 2 minutos
clock.setTime(0)       # Fuerza timeout
```

#### `addTime(delta) -> True`

Ajuste relativo. `delta` puede ser negativo. Clamp final a `>= 0`. Si el resultado es 0, entra en timeout.

```python
clock.addTime(15000)   # Agrega 15 segundos
clock.addTime(-30000)  # Quita 30 segundos
```

### Consultas

#### `getTime() -> int`

Retorna tiempo restante en ms. Si esta corriendo, sincroniza lazy antes de devolver.

```python
print(clock.getTime())  # 284321
```

#### `getSeconds() -> int`

Retorna tiempo restante en segundos (floor).

```python
print(clock.getSeconds())  # 284
```

#### `getText() -> str`

Retorna string `MM:SS` con floor. Minutos pueden exceder 59.

```python
print(clock.getText())  # '4:44'
```

**Salida:** formato `M:SS` o `MM:SS` (sin padding en minutos, con padding en segundos).

Ejemplos de salida:
- 300000 ms => `'5:00'`
- 61000 ms => `'1:01'`
- 5400000 ms => `'90:00'`
- 9500 ms => `'0:09'`

#### `isRunning() -> bool`

Indica si el reloj esta corriendo.

```python
print(clock.isRunning())  # True / False
```

#### `isTimeout() -> bool`

Indica si el tiempo llego a 0. Sincroniza lazy antes de evaluar.

```python
print(clock.isTimeout())  # True / False
```

### Callback

#### `onTimeout`

Callback opcional que se dispara una sola vez cuando el tiempo llega a 0. En timeout el reloj hace auto-pause.

```python
def tiempoAgotado():
    print("Tiempo agotado!")

clock.onTimeout = tiempoAgotado
```

| Callback | Cuando se ejecuta |
|----------|-------------------|
| `onTimeout` | Cuando el reloj llega a 0 (una sola vez por timeout) |

---

## Ejemplos

### Reloj basico

```python
from modules.chessclock import ChessClock

clock = ChessClock()
clock.start(300000)  # 5 minutos

# ... pasa tiempo ...

print(clock.getText())     # '4:32'
print(clock.isRunning())   # True

clock.pause()
print(clock.isRunning())   # False

clock.resume()
print(clock.isRunning())   # True
```

### Dos relojes (tipico en ajedrez)

```python
from modules.chessclock import ChessClock

whiteClock = ChessClock()
blackClock = ChessClock()

whiteClock.reset(300000)  # 5 min
blackClock.reset(300000)  # 5 min

# Turno de blancas
whiteClock.resume()

# ... blancas mueven ...

whiteClock.pause()
blackClock.resume()

# ... negras mueven ...

blackClock.pause()
whiteClock.resume()
```

### Usando callback de timeout

```python
from modules.chessclock import ChessClock

def blancasPierdenPorTiempo():
    print("Blancas pierden por tiempo!")

def negrasPierdenPorTiempo():
    print("Negras pierden por tiempo!")

whiteClock = ChessClock()
blackClock = ChessClock()

whiteClock.onTimeout = blancasPierdenPorTiempo
blackClock.onTimeout = negrasPierdenPorTiempo

whiteClock.start(60000)   # 1 minuto
blackClock.reset(60000)

# Polling periodico para detectar timeout
remaining = whiteClock.getTime()  # Sincroniza y puede disparar onTimeout
```

### Agregar tiempo (bonus)

```python
from modules.chessclock import ChessClock

clock = ChessClock()
clock.start(300000)

# Despues de un movimiento, agregar 5 segundos de incremento
clock.pause()
clock.addTime(5000)
# El coordinador reanuda el reloj del oponente
```

---

## Comportamiento Lazy

El descuento de tiempo NO usa timers ni threads. Se calcula al consultar o modificar estado (`getTime()`, `pause()`, `setTime()`, `addTime()`).

**Implicacion:** `onTimeout` solo se dispara durante estas llamadas. Un coordinador externo debe hacer polling periodico si necesita detectar timeout sin interaccion del usuario.

```python
import time

# Polling cada 100ms para detectar timeout
while clock.isRunning():
    clock.getTime()  # Sincroniza y puede disparar onTimeout
    time.sleep_ms(100)
```

---

## Notas

- Unidad estandar: milisegundos (int)
- `time` siempre se clamplea a `>= 0`
- `reset()` limpia el latch de timeout para nueva partida
- Metodos idempotentes: llamar `pause()` dos veces o `resume()` dos veces no rompe estado
- Compatible con MicroPython (usa `time.ticks_ms()` / `time.ticks_diff()`)
- NO ejecutar tests en CPython (requiere `ticks_ms`/`ticks_diff` de MicroPython)
