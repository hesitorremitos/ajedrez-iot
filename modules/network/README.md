# Modulo WiFi para ESP32 (MicroPython)

Modulo WiFi unificado para ESP32 que gestiona Access Point (AP) y Station (STA) de forma independiente. Permite operar en modo AP, STA, o ambos simultaneamente (AP+STA).

> **v1.1**: Operaciones async con `await` para feedback en tiempo real. Scan automático sin necesidad de `start()` previo.

## Caracteristicas

- **Operaciones async**: Usa `await` para operaciones de red no bloqueantes
- **Scan automático**: Escanea redes sin necesidad de activar STA manualmente
- **Access Point (AP)**: Crea red WiFi propia para que otros dispositivos se conecten
- **Station (STA)**: Conecta a redes WiFi existentes con auto-reconnect inteligente
- **AP+STA simultáneo**: Ambas interfaces pueden estar activas sin interferencia
- **Auto-reconnect asíncrono**: STA intenta reconectar automáticamente si pierde conexión
- **Callbacks**: onConnect, onDisconnect, onReconnectFail para reaccionar a eventos de red
- **Modo debug**: Logs detallados con prefijo `[WiFi Debug]`
- **Optimizado para ESP32**: Uso eficiente de memoria y recursos

## Instalacion

Para MicroPython en ESP32:

```python
from modules.wifi import WiFi  # Nota: import directo desde modules.wifi
import uasyncio

wifi = WiFi()

# Forma 1: Con función async
async def setup():
    await wifi.ap.start(ssid='MiRed', password='12345678')

uasyncio.run(setup())

# Forma 2: Inline (más corto)
uasyncio.run(wifi.ap.start(ssid='MiRed', password='12345678'))
```

## Testing en REPL

**⚠️ Importante**: `await` NO funciona directamente en el REPL de MicroPython porque:
- `await` solo funciona dentro de `async def`
- El REPL no tiene event loop activo por defecto
- MicroPython no soporta "top-level await"

### Cómo probar en REPL:

```python
>>> from modules.wifi import WiFi
>>> import uasyncio
>>> wifi = WiFi(debug=True)
>>> 
>>> # ❌ ESTO NO FUNCIONA (se queda congelado)
>>> await wifi.sta.scan()
>>> 
>>> # ✅ USA uasyncio.run() en su lugar:
>>> uasyncio.run(wifi.sta.scan())
[{'ssid': 'MiCasa', 'rssi': -45, ...}, ...]
>>> 
>>> # Iniciar AP
>>> uasyncio.run(wifi.ap.start(ssid="Zulma", password="12345678"))
True
>>> 
>>> # Escanear redes
>>> redes = uasyncio.run(wifi.sta.scan())
>>> print(f"Encontré {len(redes)} redes")
>>> 
>>> # Ver estado (sync, sin uasyncio.run)
>>> wifi.ap.getStatus()
{'active': True, 'ssid': 'Zulma', 'ip': '192.168.4.1'}
```

### Helper para REPL (opcional):

```python
>>> # Crear función helper corta
>>> def run(coro): return uasyncio.run(coro)
>>> 
>>> # Ahora es más corto:
>>> run(wifi.sta.scan())
>>> run(wifi.ap.start(ssid="Test"))
```

## API Publica

### Constructor

```python
wifi = WiFi(debug=False)
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `debug` | `bool` | Activa modo debug para logs de diagnostico. Default: `False` |

El constructor crea dos sub-objetos: `wifi.ap` y `wifi.sta`.

---

## Sub-objeto: wifi.ap (Access Point)

Gestiona la interfaz AP. El ESP32 crea una red WiFi propia.

### Metodos AP

#### `await ap.start(ssid, password=None, ip='192.168.4.1') -> bool` 🔄

**ASYNC**: Debe usarse con `await`

Inicia el Access Point y espera hasta que esté activo.

```python
import uasyncio

async def setup_ap():
    wifi = WiFi()
    
    # Con password (WPA2-PSK)
    success = await wifi.ap.start(ssid='Zulma', password='12345678')
    if success:
        print('AP iniciado correctamente')
    
    # Red abierta (sin password)
    await wifi.ap.start(ssid='ZulmaOpen')

uasyncio.run(setup_ap())
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `ssid` | `str` | (requerido) | Nombre de la red WiFi |
| `password` | `str \| None` | `None` | Password del AP. Si `None` o `''`, red abierta |
| `ip` | `str` | `'192.168.4.1'` | Direccion IP del AP (referencia solamente) |

**Retorna:** `True` si exitoso, `False` en caso de error.

**Comportamiento:**
- **Async**: Espera hasta que la interfaz AP esté activada (hasta 1 segundo)
- Si el AP ya esta activo, retorna `True` inmediatamente
- Password `None` o `''`: red abierta (authmode=0)
- Con password: WPA2-PSK (authmode=3)
- **Nota**: El parámetro `ip` se guarda para `getStatus()` pero MicroPython siempre usa `192.168.4.1` (no se aplica con ifconfig)

#### `ap.stop() -> bool`

**SYNC**: No requiere `await`

Detiene el Access Point.

```python
wifi.ap.stop()  # Sync, sin await
```

**Retorna:** `True` si exitoso, `False` en caso de error.

**Comportamiento:**
- Si ya esta detenido, retorna `True` (no-op)

#### `ap.getStatus() -> dict`

**SYNC**: No requiere `await`

Retorna estado actual del AP.

```python
status = wifi.ap.getStatus()  # Sync, sin await
print(status)
# {'active': True, 'ssid': 'Zulma', 'ip': '192.168.4.1'}
```

**Retorna:**
- Si activo: `{'active': True, 'ssid': str, 'ip': str}`
- Si detenido: `{'active': False, 'ssid': '', 'ip': ''}`

---

## Sub-objeto: wifi.sta (Station)

Gestiona la interfaz STA. El ESP32 se conecta a una red WiFi existente.

### Metodos de Control STA

#### `await sta.start(ssid, password=None, reconnectInterval=5000, maxReconnects=10) -> bool` 🔄

**ASYNC**: Debe usarse con `await`

Inicia conexión a red WiFi externa y **espera la conexión inicial** (hasta 10 segundos).

```python
import uasyncio

async def connect_wifi():
    wifi = WiFi(debug=True)
    
    # Conexion basica (espera hasta conectar)
    success = await wifi.sta.start(ssid='MiCasa', password='wifi123')
    if success and wifi.sta.isConnected():
        print('Conectado!')
    
    # Red abierta
    await wifi.sta.start(ssid='CafePublico')
    
    # Con parametros de auto-reconnect personalizados
    await wifi.sta.start(
        ssid='MiCasa',
        password='wifi123',
        reconnectInterval=10000,  # 10 segundos entre reintentos
        maxReconnects=5           # maximo 5 intentos
    )

uasyncio.run(connect_wifi())
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `ssid` | `str` | (requerido) | Nombre de la red WiFi |
| `password` | `str \| None` | `None` | Password de la red. `None` para redes abiertas |
| `reconnectInterval` | `int` | `5000` | Milisegundos entre reintentos de conexion |
| `maxReconnects` | `int` | `10` | Numero maximo de reintentos antes de rendirse |

**Retorna:** `True` si se inició correctamente, `False` en caso de error.

**Comportamiento:**
- **Async**: Espera hasta conectarse o timeout (10 segundos)
- Activa STA_IF y lanza tarea async de monitoreo/reconexion
- Si se pierde la conexion, reintenta automaticamente
- Tras `maxReconnects` intentos fallidos: dispara `onReconnectFail()` y se desactiva
- Si se llama `start()` cuando ya esta activo: reinicia con nuevos parametros

#### `await sta.stop() -> bool` 🔄

**ASYNC**: Debe usarse con `await`

Desconecta de la red WiFi y cancela auto-reconnect.

```python
await wifi.sta.stop()  # Async, con await
```

**Retorna:** `True` si exitoso, `False` en caso de error.

**Comportamiento:**
- **Async**: Cancela y espera la tarea async de monitoreo
- Desactiva STA_IF
- Si ya esta detenido, retorna `True` (no-op)

### Metodos de Consulta STA

#### `sta.isConnected() -> bool`

Retorna `True` si STA esta conectado a una red WiFi.

```python
if wifi.sta.isConnected():
    print("Conectado a internet")
```

#### `sta.getStatus() -> dict`

Retorna estado actual de STA.

```python
status = wifi.sta.getStatus()
print(status)
# {'connected': True, 'ssid': 'MiCasa', 'ip': '192.168.1.105'}
```

**Retorna:**
- Si conectado: `{'connected': True, 'ssid': str, 'ip': str}`
- Si no conectado: `{'connected': False, 'ssid': '', 'ip': ''}`

#### `await sta.scan() -> list[dict]` 🔄

**ASYNC**: Debe usarse con `await`

Escanea redes WiFi disponibles. **Activa automáticamente STA_IF** si es necesario.

```python
import uasyncio

async def buscar_redes():
    wifi = WiFi()
    
    # Ya NO necesitas llamar start() antes de scan()
    # scan() activa STA automáticamente
    redes = await wifi.sta.scan()
    
    print(f"Encontré {len(redes)} redes:")
    for red in redes:
        print(f"  {red['ssid']}: {red['rssi']} dBm, Canal {red['channel']}")

uasyncio.run(buscar_redes())
```

**Retorna:** Lista de dicts con información de cada red.

```python
[
    {
        'ssid': 'MiCasa',
        'rssi': -45,
        'channel': 6,
        'security': 3,
        'bssid': 'aa:bb:cc:dd:ee:ff'
    },
    {
        'ssid': 'Vecino_5G',
        'rssi': -72,
        'channel': 36,
        'security': 3,
        'bssid': '11:22:33:44:55:66'
    }
]
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `ssid` | `str` | Nombre de la red |
| `rssi` | `int` | Intensidad de señal (dBm). Más cercano a 0 = mejor |
| `channel` | `int` | Canal WiFi |
| `security` | `int` | Tipo de autenticacion (0=open, 1=WEP, 2=WPA-PSK, 3=WPA2-PSK, 4=WPA/WPA2-PSK) |
| `bssid` | `str` | MAC del access point en formato `aa:bb:cc:dd:ee:ff` |

**Comportamiento:**
- **Async**: Espera inicialización de STA_IF y escaneo completo
- **✨ Activa automáticamente STA_IF** si no está activo (no necesitas llamar `start()` antes)
- **Temporalmente desactiva AP** durante el scan para mejores resultados (limitación ESP32)
- Reactiva AP después del scan si estaba activo antes
- Filtra SSIDs vacíos y ocultos
- Elimina duplicados por SSID (conserva entrada con mejor RSSI)

### Callbacks STA

#### `sta.onConnect`

Se dispara cuando STA se conecta exitosamente a la red WiFi.

```python
def connected(ip):
    print(f"Conectado con IP: {ip}")

wifi.sta.onConnect = connected
wifi.sta.start(ssid='MiCasa', password='wifi123')
```

**Firma:** `onConnect(ip: str)`

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `ip` | `str` | Direccion IP asignada al ESP32 por DHCP |

**Comportamiento:**
- Se dispara tanto en conexion inicial como en reconexiones exitosas
- Callback opcional. Si es `None`, no se dispara

#### `sta.onDisconnect`

Se dispara cuando STA pierde la conexion a la red WiFi.

```python
def disconnected():
    print("Se perdio la conexion WiFi")

wifi.sta.onDisconnect = disconnected
```

**Firma:** `onDisconnect()`

**Comportamiento:**
- Sin parametros
- Se dispara una vez por evento de desconexion, no por cada reintento
- Callback opcional. Si es `None`, no se dispara

#### `sta.onReconnectFail`

Se dispara cuando se agotan los intentos de reconexion.

```python
def reconnectFailed():
    print("No se pudo reconectar. Intente manualmente.")

wifi.sta.onReconnectFail = reconnectFailed
```

**Firma:** `onReconnectFail()`

**Comportamiento:**
- Sin parametros
- Despues de dispararse: STA_IF se desactiva y la tarea async termina
- Para reintentar, el usuario debe llamar `sta.start()` de nuevo
- Callback opcional. Si es `None`, no se dispara

---

## Ejemplos de Uso

### Ejemplo 1: Solo Access Point (forma corta)

```python
from modules.wifi import WiFi
import uasyncio

wifi = WiFi()

# Forma corta con uasyncio.run() directo
uasyncio.run(wifi.ap.start(ssid='Zulma', password='12345678'))

# Consultar estado (sync, sin uasyncio.run)
status = wifi.ap.getStatus()
print(f"AP activo: {status['active']}")
print(f"SSID: {status['ssid']}")
print(f"IP: {status['ip']}")
```

### Ejemplo 1b: Access Point con loop (forma completa)

```python
from modules.wifi import WiFi
import uasyncio

async def setup_ap():
    wifi = WiFi()
    
    # Iniciar AP con password (espera hasta que esté activo)
    success = await wifi.ap.start(ssid='Zulma', password='12345678')
    
    if success:
        print("AP activo:", wifi.ap.getStatus())
    
    # Mantener AP activo
    while True:
        await uasyncio.sleep(10)

uasyncio.run(setup_ap())
```

### Ejemplo 2: Solo Station con callbacks

```python
from modules.wifi import WiFi
import uasyncio

wifi = WiFi(debug=True)

# Registrar callbacks
wifi.sta.onConnect = lambda ip: print(f"Conectado: {ip}")
wifi.sta.onDisconnect = lambda: print("Desconectado")
wifi.sta.onReconnectFail = lambda: print("Fallo al reconectar")

# Conectar (forma corta)
uasyncio.run(wifi.sta.start(ssid='MiCasa', password='wifi123'))

# Ver estado
print("Estado:", wifi.sta.getStatus())
print("Conectado:", wifi.sta.isConnected())
```

### Ejemplo 3: AP+STA simultáneo (forma corta)

```python
from modules.wifi import WiFi
import uasyncio

wifi = WiFi()

# Iniciar ambos con uasyncio.run inline
uasyncio.run(wifi.ap.start(ssid='Zulma-Config', password='config123'))
uasyncio.run(wifi.sta.start(ssid='MiCasa', password='wifi123'))

# Verificar estados (sync)
print("AP:", wifi.ap.getStatus())
print("STA:", wifi.sta.getStatus())
```
    
    # Ambos activos simultaneamente (sync checks)
    apStatus = wifi.ap.getStatus()
    staStatus = wifi.sta.getStatus()
    
    print(f"AP: {apStatus['active']} en {apStatus['ip']}")
    print(f"STA: {staStatus['connected']} con IP {staStatus['ip']}")
    
    while True:
        await uasyncio.sleep(10)

uasyncio.run(setup_dual_mode())
```

### Ejemplo 4: Escanear redes disponibles (forma corta)

```python
from modules.wifi import WiFi
import uasyncio

wifi = WiFi()

# Forma corta - scan automático (sin activar STA manualmente)
redes = uasyncio.run(wifi.sta.scan())

print(f"Encontré {len(redes)} redes:")
for red in redes[:5]:  # Mostrar top 5
    print(f"  {red['ssid']}: {red['rssi']} dBm, Canal {red['channel']}")
```

### Ejemplo 5: Cambiar de red WiFi (forma corta)

```python
from modules.wifi import WiFi
import uasyncio

wifi = WiFi()

# Conectar a primera red
uasyncio.run(wifi.sta.start(ssid='MiCasa', password='wifi123'))
print("Conectado a MiCasa:", wifi.sta.isConnected())

# Cambiar a otra red (reinicia automaticamente)
uasyncio.run(wifi.sta.start(ssid='OtraRed', password='otra123'))
print("Conectado a OtraRed:", wifi.sta.isConnected())
```

### Ejemplo 6: Auto-reconnect personalizado

```python
from modules.wifi import WiFi
import uasyncio

async def setup_with_auto_reset():
    wifi = WiFi(debug=True)
    
    def reconnectFailed():
        print("Fallo tras 3 intentos. Reiniciando ESP32...")
        import machine
        machine.reset()
    
    wifi.sta.onReconnectFail = reconnectFailed
    
    # Solo 3 intentos, cada 10 segundos
    await wifi.sta.start(
        ssid='MiCasa',
        password='wifi123',
        reconnectInterval=10000,
        maxReconnects=3
    )
    
    while True:
        await uasyncio.sleep(10)

uasyncio.run(setup_with_auto_reset())
```

---

## Modo Debug

Activa logs detallados con prefijo `[WiFi Debug]`:

```python
wifi = WiFi(debug=True)
```

**Eventos loggeados:**
- AP: start, stop, errores
- STA: start, conexion exitosa, desconexion, reintentos, reconnect fail, stop
- Scan: cantidad de redes encontradas

**Ejemplo de output:**
```
[WiFi Debug] AP started: Zulma on 192.168.4.1
[WiFi Debug] STA connecting to: MiCasa
[WiFi Debug] STA connected, IP: 192.168.1.105
[WiFi Debug] STA disconnected
[WiFi Debug] STA reconnect attempt 1 of 10
[WiFi Debug] STA connected, IP: 192.168.1.105
```

---

## Manejo de Errores

- **Sin excepciones custom**: los metodos `start()` y `stop()` retornan `True`/`False`
- **Sin validacion de parametros**: SSID, password e IP se pasan directamente a MicroPython
- Si MicroPython lanza excepcion interna, el modulo la captura y retorna `False`
- Consistente con patron del proyecto (Chess, ChessClock)

```python
result = wifi.ap.start(ssid='Test', password='12345678')
if result:
    print("AP iniciado correctamente")
else:
    print("Error al iniciar AP")
```

---

## Independencia AP/STA

Las interfaces AP y STA son **completamente independientes**:

- `ap.start()` NO toca STA_IF
- `sta.start()` NO toca AP_IF
- Ambas pueden estar activas simultaneamente
- No hay orden requerido para iniciarlas
- Detener una NO afecta la otra

```python
wifi = WiFi()

# Cualquier combinacion es valida
wifi.ap.start(ssid='AP')
wifi.sta.start(ssid='STA', password='pass')

# Detener una no afecta la otra
wifi.ap.stop()  # STA sigue conectado
wifi.sta.stop()  # AP sigue activo (si se reinicio)
```

---

## Casos de Uso Tipicos

### 1. Portal de Configuracion

```python
wifi = WiFi()

# AP para que usuario se conecte y configure
wifi.ap.start(ssid='Zulma-Setup', password='setup123')

# Servidor web escucha en 192.168.4.1
# Usuario ingresa credenciales WiFi

# Cuando se reciben credenciales, conectar a red externa
wifi.sta.start(ssid=credenciales['ssid'], password=credenciales['password'])

# Opcional: mantener AP activo para reconfigurar
# o cerrarlo con wifi.ap.stop()
```

### 2. Cliente MQTT con AP de emergencia

```python
wifi = WiFi()

def staConnected(ip):
    print(f"Conectado a red: {ip}")
    # Iniciar cliente MQTT

def reconnectFailed():
    print("No hay red WiFi. Activando AP de emergencia")
    wifi.ap.start(ssid='Zulma-Emergency', password='emergency')

wifi.sta.onConnect = staConnected
wifi.sta.onReconnectFail = reconnectFailed

wifi.sta.start(ssid='MiCasa', password='wifi123', maxReconnects=5)
```

### 3. Modo Dual Permanente

```python
wifi = WiFi()

# AP para acceso local directo
wifi.ap.start(ssid='Zulma-Local', password='local123')

# STA para acceso remoto via internet
wifi.sta.start(ssid='MiCasa', password='wifi123')

# Dispositivo accesible tanto localmente (192.168.4.1)
# como remotamente (IP asignada por router)
```

---

## Notas Tecnicas

- Compatible con MicroPython para ESP32
- Guarda imports para compatibilidad con tests CPython:
  - `try: import network` / `except ImportError: network = None`
  - `try: import uasyncio` / `except ImportError: import asyncio as uasyncio`
- Auto-reconnect usa tarea async (`uasyncio.create_task`)
- Optimizado para memoria limitada (ESP32)
- Naming: camelCase para API pública (por diseño del proyecto)

---

## Pruebas

```bash
# Tests completos del modulo WiFi
uv run pytest tests/modules/network/test_wifi.py -v

# Suite completa del proyecto
uv run pytest
```

Las pruebas cubren:
- AP: start, stop, getStatus con parametros variados
- STA: start, stop, isConnected, getStatus, scan
- Callbacks: onConnect, onDisconnect, onReconnectFail
- Independencia: AP y STA simultaneos sin interferencia
- Modo debug: logs correctos

---

## Version

**1.1 - Febrero 2026**

Cambios principales:
- **Operaciones async**: Todos los métodos de red son async (requieren `await` o `uasyncio.run()`)
- **Scan automático**: `scan()` activa STA automáticamente si es necesario
- **Fix DHCP**: Eliminada llamada a `ifconfig()` que rompía DHCP del AP
- **Testing mejorado**: Documentación completa para uso en REPL con `uasyncio.run()`

**1.0 - Febrero 2026**

Versión inicial que reemplaza módulo `AccessPoint` con arquitectura unificada WiFi (AP + STA).
