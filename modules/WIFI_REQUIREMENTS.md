---
last_updated: "2026-02-11 13:00"
version: "1.1"
status: draft
author: Discovery Architect
---

# WiFi Module - Documento de Requerimientos

> **Reemplaza**: `ACCESSPOINT_REQUIREMENTS.md` y el modulo `AccessPoint`. Este documento describe un modulo de red WiFi unificado que gestiona AP y STA de forma independiente.

## Descripcion General

Modulo WiFi unificado para ESP32 (MicroPython) que controla la red inalambrica WiFi. Permite operar en modo Access Point (AP), modo Station (STA), o ambos simultaneamente (AP+STA). Cada interfaz se gestiona a traves de sub-objetos independientes (`wifi.ap` y `wifi.sta`).

El modulo es de uso general. Casos de uso previstos:
- AP para portal de configuracion (servidor web local).
- STA para conectar a red externa y comunicarse con broker MQTT.
- AP+STA simultaneo para configurar el ESP32 mientras mantiene conexion a la red externa.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32.
- Optimizar uso de memoria RAM y CPU.
- camelCase para todos los nombres de metodos y propiedades.
- Ubicacion del archivo: `modules/network/WiFi.py`
- Nombre de la clase principal: `WiFi`
- Sub-objetos internos: `_Ap` y `_Sta` (clases privadas en el mismo archivo).
- Patron de errores: return codes (`True`/`False`), sin excepciones custom.

---

## Arquitectura

```
WiFi (clase principal)
  |
  +-- ap (_Ap)      # Sub-objeto para Access Point
  |     start(), stop(), getStatus()
  |
  +-- sta (_Sta)    # Sub-objeto para Station
        start(), stop(), scan(), isConnected(), getStatus()
        onConnect, onDisconnect, onReconnectFail (callbacks)
```

### Principio de independencia

- `ap.start()` NO toca STA_IF.
- `sta.start()` NO toca AP_IF.
- Ambas interfaces pueden estar activas simultaneamente.
- No hay orden requerido para iniciarlas.

---

## API Publica

### Constructor

```python
WiFi(debug=False)
```

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `debug` | `bool` | `False` | Habilita logs de diagnostico con prefijo `[WiFi Debug]` |

El constructor es vacio (sin config de red). Toda la configuracion se pasa en los metodos `start()` de cada sub-objeto.

### Atributos publicos

| Atributo | Tipo | Descripcion |
|----------|------|-------------|
| `ap` | `_Ap` | Sub-objeto para gestionar Access Point |
| `sta` | `_Sta` | Sub-objeto para gestionar Station |

---

## Sub-objeto: wifi.ap (_Ap)

Gestiona la interfaz AP (Access Point). El ESP32 crea una red WiFi propia a la que otros dispositivos se conectan.

### Metodos

#### ap.start(ssid, password=None, ip='192.168.4.1')

Inicia el Access Point.

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `ssid` | `str` | (requerido) | Nombre de la red WiFi |
| `password` | `str \| None` | `None` | Password del AP. Si `None` o `''`, red abierta (sin auth) |
| `ip` | `str` | `'192.168.4.1'` | Direccion IP del AP |

Comportamiento:
- Activa `network.AP_IF`.
- Configura SSID, password y modo de autenticacion.
  - Password `None` o `''`: red abierta (`authmode=0`).
  - Con password: WPA2-PSK (`authmode=3`).
- Configura IP del AP con `ifconfig()`.
- Si el AP ya esta activo, retorna `True` sin hacer nada (no-op).
- Retorna `True` si exitoso, `False` en caso de error.

#### ap.stop()

Detiene el Access Point.

- Desactiva `network.AP_IF`.
- Si ya esta detenido, retorna `True` (no-op).
- Retorna `True` si exitoso, `False` en caso de error.

#### ap.getStatus()

Retorna estado actual del AP.

```python
{
    'active': True,       # bool - si el AP esta activo
    'ssid': 'Zulma',      # str - nombre de la red
    'ip': '192.168.4.1'   # str - direccion IP del AP
}
```

Si el AP esta detenido:
```python
{
    'active': False,
    'ssid': '',
    'ip': ''
}
```

---

## Sub-objeto: wifi.sta (_Sta)

Gestiona la interfaz STA (Station). El ESP32 se conecta a una red WiFi existente.

### Metodos de Control

#### sta.start(ssid, password=None, reconnectInterval=5000, maxReconnects=10)

Inicia conexion a red WiFi externa. **No bloqueante**.

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `ssid` | `str` | (requerido) | Nombre de la red WiFi a conectar |
| `password` | `str \| None` | `None` | Password de la red. `None` para redes abiertas |
| `reconnectInterval` | `int` | `5000` | Milisegundos entre reintentos de conexion |
| `maxReconnects` | `int` | `10` | Numero maximo de reintentos antes de rendirse |

Comportamiento:
1. Activa `network.STA_IF`.
2. Inicia conexion a la red indicada.
3. Lanza una **tarea async interna** (`uasyncio.create_task`) que:
   - Monitorea el estado de conexion.
   - Si se pierde la conexion, reintenta automaticamente.
   - Respeta `reconnectInterval` entre intentos.
   - Tras `maxReconnects` intentos fallidos consecutivos:
     - Dispara `onReconnectFail()` (si hay callback registrado).
     - Desactiva STA_IF.
     - La tarea async termina.
4. Retorna `True` si se inicio el intento, `False` en caso de error.

**Si se llama `start()` cuando ya esta activo:**
- Detiene la tarea async actual (equivalente a `stop()` interno).
- Reinicia con los nuevos parametros proporcionados.
- Esto permite cambiar de red WiFi sin llamar `stop()` manualmente.

#### sta.stop()

Desconecta de la red WiFi y cancela la tarea async de auto-reconnect.

- Cancela la tarea async de monitoreo/reconexion.
- Desactiva `network.STA_IF`.
- Si ya esta detenido, retorna `True` (no-op).
- Retorna `True` si exitoso, `False` en caso de error.

### Metodos de Consulta

#### sta.isConnected()

Retorna `bool`. `True` si STA esta conectado a una red WiFi.

Consulta directa a `network.WLAN(STA_IF).isconnected()`. Sin overhead.

#### sta.getStatus()

Retorna estado actual de STA.

```python
{
    'connected': True,           # bool - si esta conectado
    'ssid': 'MiCasa',           # str - nombre de la red
    'ip': '192.168.1.105'       # str - IP asignada por DHCP
}
```

Si STA no esta conectado:
```python
{
    'connected': False,
    'ssid': '',
    'ip': ''
}
```

#### sta.scan()

Escanea redes WiFi disponibles.

- **Requiere STA_IF activo** (que se haya llamado `sta.start()` previamente).
- Si STA_IF no esta activo, retorna lista vacia `[]`.
- Retorna lista de dicts con informacion completa de cada red (`list[dict]`).
- Filtra SSIDs vacios y ocultos.
- Elimina duplicados por SSID (conserva la entrada con mejor RSSI).

Formato de retorno:
```python
wifi.sta.scan()
# [
#     {'ssid': 'MiCasa', 'rssi': -45, 'channel': 6, 'security': 3, 'bssid': 'aa:bb:cc:dd:ee:ff'},
#     {'ssid': 'Vecino_5G', 'rssi': -72, 'channel': 36, 'security': 3, 'bssid': '11:22:33:44:55:66'},
#     {'ssid': 'CafeWiFi', 'rssi': -80, 'channel': 1, 'security': 0, 'bssid': '77:88:99:aa:bb:cc'},
# ]
```

Campos del dict:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `ssid` | `str` | Nombre de la red |
| `rssi` | `int` | Intensidad de senal (dBm). Mas cercano a 0 = mejor |
| `channel` | `int` | Canal WiFi |
| `security` | `int` | Tipo de autenticacion (valor nativo MicroPython: 0=open, 1=WEP, 2=WPA-PSK, 3=WPA2-PSK, 4=WPA/WPA2-PSK) |
| `bssid` | `str` | MAC del access point en formato `aa:bb:cc:dd:ee:ff` |

### Callbacks

#### sta.onConnect

Se dispara cuando STA se conecta exitosamente a la red WiFi.

Firma:
```python
def onConnect(ip):
    pass
```

| Parametro | Tipo | Descripcion |
|-----------|------|-------------|
| `ip` | `str` | Direccion IP asignada al ESP32 por DHCP |

- Se dispara tanto en la conexion inicial como en reconexiones exitosas.
- Callback opcional. Si es `None`, no se dispara.

#### sta.onDisconnect

Se dispara cuando STA pierde la conexion a la red WiFi.

Firma:
```python
def onDisconnect():
    pass
```

- Sin parametros. Consistente con otros callbacks del proyecto (Chess, ChessClock).
- Se dispara una vez por evento de desconexion, no por cada reintento.
- Callback opcional. Si es `None`, no se dispara.

#### sta.onReconnectFail

Se dispara cuando se agotan los `maxReconnects` intentos de reconexion.

Firma:
```python
def onReconnectFail():
    pass
```

- Sin parametros.
- Despues de dispararse:
  - STA_IF se desactiva.
  - La tarea async de auto-reconnect termina.
  - Para reintentar, el usuario debe llamar `sta.start()` de nuevo.
- Callback opcional. Si es `None`, no se dispara (STA se detiene silenciosamente).

---

## Modo Debug

- Propiedad en constructor: `WiFi(debug=True)`.
- Mensajes con prefijo `[WiFi Debug]`.
- Eventos loggeados:
  - AP: start, stop, error.
  - STA: start, conexion exitosa, desconexion, reintento N de M, reconnect fail, stop.
  - Scan: cantidad de redes encontradas.

---

## Manejo de Errores

- **Sin excepciones custom**: el modulo usa return codes (`True`/`False`).
- **Sin validacion de parametros**: SSID, password e IP se pasan directamente a la API de MicroPython `network.WLAN`.
- Si MicroPython lanza una excepcion interna (ej: hardware no disponible), el modulo la captura y retorna `False`.
- Consistente con patron existente en Chess (`play()` retorna bool) y AccessPoint.

---

## Edge Cases

### AP
- `ap.start()` cuando ya activo: no-op, retorna `True`.
- `ap.stop()` cuando ya detenido: no-op, retorna `True`.
- `ap.start()` con password vacio `''`: red abierta (sin auth).
- `ap.getStatus()` antes de start: retorna `{active: False, ssid: '', ip: ''}`.

### STA
- `sta.start()` cuando ya activo: reinicia conexion con nuevos parametros.
- `sta.stop()` cuando ya detenido: no-op, retorna `True`.
- `sta.scan()` sin STA_IF activo: retorna `[]`.
- `sta.isConnected()` antes de start: retorna `False`.
- `sta.getStatus()` antes de start: retorna `{connected: False, ssid: '', ip: ''}`.
- `sta.start()` seguido de `sta.stop()` inmediato: cancela tarea async limpiamente.
- Red WiFi desaparece: auto-reconnect intenta hasta `maxReconnects`, luego `onReconnectFail`.
- Multiples `start()` rapidos: cada uno cancela el anterior y reinicia.

### AP+STA simultaneo
- Ambos pueden estar activos sin interferencia.
- No hay orden requerido para iniciarlos.
- Detener uno no afecta al otro.

---

## Estructura de Archivos

```text
modules/
  WIFI_REQUIREMENTS.md           # Este documento
  ACCESSPOINT_REQUIREMENTS.md    # Obsoleto (reemplazado por este)
  network/
    __init__.py                  # Exporta WiFi (elimina export de AccessPoint)
    WiFi.py                      # Clase WiFi + _Ap + _Sta (archivo unico)
    AccessPoint.py               # Obsoleto (eliminar)

tests/
  modules/
    network/
      test_wifi.py               # Tests nuevos (reescritura completa)
      test_access_point.py       # Obsoleto (eliminar)
```

### Migracion

1. Crear `WiFi.py` con clases `WiFi`, `_Ap`, `_Sta`.
2. Actualizar `__init__.py`: exportar `WiFi`, eliminar `AccessPoint`.
3. Eliminar `AccessPoint.py`.
4. Reescribir tests en `test_wifi.py`.
5. Eliminar `test_access_point.py`.
6. Actualizar `AGENTS.md` si lista `sse` como modulo primario (se reemplaza por mqtt eventualmente).

---

## Ejemplo de Uso

### Solo AP

```python
from modules.network import WiFi

wifi = WiFi()
wifi.ap.start(ssid='Zulma', password='12345678')
wifi.ap.getStatus()  # {'active': True, 'ssid': 'Zulma', 'ip': '192.168.4.1'}
wifi.ap.stop()
```

### Solo STA

```python
from modules.network import WiFi

wifi = WiFi(debug=True)

wifi.sta.onConnect = lambda ip: print(f"Conectado: {ip}")
wifi.sta.onDisconnect = lambda: print("Desconectado")
wifi.sta.onReconnectFail = lambda: print("No se pudo reconectar")

wifi.sta.start(ssid='MiCasa', password='wifi123')
# No bloquea. La conexion ocurre en background.
# onConnect se dispara cuando se establece conexion.
```

### AP+STA simultaneo

```python
from modules.network import WiFi

wifi = WiFi()

# AP para portal de configuracion
wifi.ap.start(ssid='Zulma-Config', password='config123')

# STA para conexion a red externa
wifi.sta.onConnect = lambda ip: print(f"STA conectado: {ip}")
wifi.sta.start(ssid='MiCasa', password='wifi123')

# Ambos activos simultaneamente
wifi.ap.getStatus()   # {'active': True, 'ssid': 'Zulma-Config', 'ip': '192.168.4.1'}
wifi.sta.getStatus()  # {'connected': True, 'ssid': 'MiCasa', 'ip': '192.168.1.105'}
```

### Scan de redes

```python
wifi = WiFi()
wifi.sta.start(ssid='temporal', password='xxx')  # Activa STA_IF
redes = wifi.sta.scan()
# [
#     {'ssid': 'MiCasa', 'rssi': -45, 'channel': 6, 'security': 3, 'bssid': 'aa:bb:cc:dd:ee:ff'},
#     {'ssid': 'Vecino_5G', 'rssi': -72, 'channel': 36, 'security': 3, 'bssid': '11:22:33:44:55:66'},
# ]
```

### Cambiar de red WiFi

```python
wifi.sta.start(ssid='MiCasa', password='wifi123')
# ... mas tarde, cambiar a otra red:
wifi.sta.start(ssid='OtraRed', password='otra123')  # Reinicia con nuevos params
```

### Configuracion de auto-reconnect

```python
wifi.sta.start(
    ssid='MiCasa',
    password='wifi123',
    reconnectInterval=10000,  # 10 segundos entre reintentos
    maxReconnects=5            # maximo 5 intentos
)
```

---

## Criterios de Aceptacion

### AP

#### AC-01: ap.start() inicia AP correctamente
- **Given** instancia de WiFi sin AP activo
- **When** se llama `wifi.ap.start(ssid='Test', password='12345678')`
- **Then** retorna `True`, AP_IF activo, SSID y password configurados, authmode WPA2

#### AC-02: ap.start() red abierta sin password
- **Given** instancia de WiFi
- **When** se llama `wifi.ap.start(ssid='Open')` o `wifi.ap.start(ssid='Open', password='')`
- **Then** retorna `True`, AP_IF activo, authmode=0 (red abierta)

#### AC-03: ap.start() con IP personalizada
- **Given** instancia de WiFi
- **When** se llama `wifi.ap.start(ssid='Test', ip='10.0.0.1')`
- **Then** retorna `True`, AP_IF configurado con IP 10.0.0.1

#### AC-04: ap.start() no-op cuando ya activo
- **Given** AP ya iniciado
- **When** se llama `ap.start()` nuevamente
- **Then** retorna `True` sin reiniciar el AP

#### AC-05: ap.stop() detiene AP
- **Given** AP activo
- **When** se llama `ap.stop()`
- **Then** retorna `True`, AP_IF desactivado

#### AC-06: ap.stop() no-op cuando detenido
- **Given** AP ya detenido
- **When** se llama `ap.stop()`
- **Then** retorna `True`

#### AC-07: ap.getStatus() activo
- **Given** AP activo con ssid='Test', ip='192.168.4.1'
- **When** se llama `ap.getStatus()`
- **Then** retorna `{'active': True, 'ssid': 'Test', 'ip': '192.168.4.1'}`

#### AC-08: ap.getStatus() detenido
- **Given** AP no iniciado
- **When** se llama `ap.getStatus()`
- **Then** retorna `{'active': False, 'ssid': '', 'ip': ''}`

#### AC-09: ap.start() retorna False en error
- **Given** hardware WiFi no disponible (mock lanza excepcion)
- **When** se llama `ap.start(ssid='Test')`
- **Then** retorna `False` sin propagar excepcion

### STA

#### AC-10: sta.start() inicia conexion no bloqueante
- **Given** instancia de WiFi
- **When** se llama `wifi.sta.start(ssid='Red', password='pass')`
- **Then** retorna `True` inmediatamente, STA_IF activado, tarea async de conexion/reconnect lanzada

#### AC-11: sta.start() reinicia si ya activo
- **Given** STA ya conectado a 'RedA'
- **When** se llama `sta.start(ssid='RedB', password='pass')`
- **Then** detiene conexion anterior, reinicia con nuevos parametros

#### AC-12: sta.stop() desconecta y cancela auto-reconnect
- **Given** STA activo con tarea async de reconnect
- **When** se llama `sta.stop()`
- **Then** retorna `True`, STA_IF desactivado, tarea async cancelada

#### AC-13: sta.stop() no-op cuando detenido
- **Given** STA no iniciado
- **When** se llama `sta.stop()`
- **Then** retorna `True`

#### AC-14: sta.isConnected() retorna estado correcto
- **Given** STA conectado a una red
- **When** se llama `sta.isConnected()`
- **Then** retorna `True`

#### AC-15: sta.isConnected() sin conexion
- **Given** STA no iniciado o desconectado
- **When** se llama `sta.isConnected()`
- **Then** retorna `False`

#### AC-16: sta.getStatus() conectado
- **Given** STA conectado a 'MiCasa' con IP '192.168.1.105'
- **When** se llama `sta.getStatus()`
- **Then** retorna `{'connected': True, 'ssid': 'MiCasa', 'ip': '192.168.1.105'}`

#### AC-17: sta.getStatus() desconectado
- **Given** STA no iniciado
- **When** se llama `sta.getStatus()`
- **Then** retorna `{'connected': False, 'ssid': '', 'ip': ''}`

#### AC-18: sta.scan() retorna info completa sin duplicados
- **Given** STA_IF activo, redes visibles incluyen duplicados del mismo SSID
- **When** se llama `sta.scan()`
- **Then** retorna lista de dicts con ssid, rssi, channel, security, bssid. Sin duplicados por SSID (conserva mejor RSSI). Sin SSIDs vacios ni ocultos

#### AC-19: sta.scan() sin STA_IF activo retorna vacio
- **Given** STA_IF no activo (no se llamo sta.start())
- **When** se llama `sta.scan()`
- **Then** retorna `[]`

### Callbacks STA

#### AC-20: onConnect se dispara con IP
- **Given** callback registrado en `sta.onConnect`
- **When** STA se conecta exitosamente
- **Then** `onConnect(ip)` se dispara con la IP asignada

#### AC-21: onDisconnect se dispara sin parametros
- **Given** callback registrado en `sta.onDisconnect`, STA conectado
- **When** se pierde la conexion WiFi
- **Then** `onDisconnect()` se dispara una vez

#### AC-22: onReconnectFail tras agotar intentos
- **Given** callback registrado, `maxReconnects=3`, red inalcanzable
- **When** se agotan los 3 intentos de reconexion
- **Then** `onReconnectFail()` se dispara, STA_IF se desactiva, tarea async termina

#### AC-23: onConnect en reconexion exitosa
- **Given** callback registrado, STA reconecta automaticamente tras perdida
- **When** la reconexion tiene exito
- **Then** `onConnect(ip)` se dispara con la nueva IP

### Independencia AP/STA

#### AC-24: ap.start() no afecta STA
- **Given** STA conectado
- **When** se llama `ap.start(ssid='AP')`
- **Then** STA sigue conectado, AP se activa

#### AC-25: sta.start() no afecta AP
- **Given** AP activo
- **When** se llama `sta.start(ssid='Red')`
- **Then** AP sigue activo, STA inicia conexion

#### AC-26: ap.stop() no afecta STA
- **Given** AP y STA ambos activos
- **When** se llama `ap.stop()`
- **Then** AP se detiene, STA sigue conectado

#### AC-27: sta.stop() no afecta AP
- **Given** AP y STA ambos activos
- **When** se llama `sta.stop()`
- **Then** STA se detiene, AP sigue activo

### Debug

#### AC-28: debug mode logs eventos
- **Given** `WiFi(debug=True)`
- **When** se ejecutan operaciones (start, connect, disconnect, scan)
- **Then** se imprimen mensajes con prefijo `[WiFi Debug]`

### Error Handling

#### AC-29: sta.start() retorna False en error de hardware
- **Given** hardware WiFi no disponible
- **When** se llama `sta.start(ssid='Red')`
- **Then** retorna `False` sin propagar excepcion

---

## Funcionalidad Excluida (fuera de alcance)

- Captive portal.
- Servidor web/HTTP integrado.
- MQTT (sera modulo separado).
- Persistencia de configuracion entre reinicios.
- Configuracion de canal WiFi.
- Validacion de parametros de entrada (longitud password, caracteres SSID).
- TLS/SSL para conexiones WiFi (WPA Enterprise).
- Metodo `configure()` (reconfigurar = `stop()` + `start()` con nuevos params; en STA, basta con llamar `start()` de nuevo).
- Gestion de clientes AP (`getClients`, `getClientsInfo`, `clientCount`).
- `getStatus()` a nivel raiz WiFi (solo en sub-objetos).

---

## Decisions Log

| Fecha | Decision | Alternativas Consideradas | Razon |
|-------|----------|---------------------------|-------|
| 2026-02-11 | Renombrar de AccessPoint a WiFi | WiFiManager, Network | Simple, directo, describe responsabilidad |
| 2026-02-11 | Sub-objetos wifi.ap / wifi.sta | Metodos separados (startAp/startSta), parametro mode, clase unica | Mas legible, API descubrible, separacion clara (~100B extra RAM aceptable) |
| 2026-02-11 | AP y STA independientes | AP desactiva STA (patron anterior), modo exclusivo | Necesario para AP+STA simultaneo (portal config + red externa) |
| 2026-02-11 | Eliminar configure() | Mantener configure() con apply inmediato | Redundante: stop()+start() logra lo mismo. En STA, start() ya reinicia |
| 2026-02-11 | Eliminar getClients/getClientsInfo/clientCount | Mantener funcionalidad de clientes | No necesario para los casos de uso actuales. Simplifica API |
| 2026-02-11 | Constructor vacio WiFi() | Config en constructor | Flexibilidad: cada interfaz se configura independientemente |
| 2026-02-11 | sta.start() no bloqueante + tarea async | Bloqueante con timeout, configurable | Consistente con arquitectura uasyncio del proyecto. No bloquea coordinador |
| 2026-02-11 | Auto-reconnect con tarea async interna | Polling externo, manual | Encapsula logica de reconexion. stop() cancela la tarea |
| 2026-02-11 | Callbacks: onConnect(ip), onDisconnect(), onReconnectFail() | Solo polling, solo callbacks | Complementario: callbacks para reaccionar + isConnected() para consulta |
| 2026-02-11 | onConnect recibe IP como parametro | Sin parametros (como Chess) | IP es dato util que evita llamada extra a getStatus() |
| 2026-02-11 | scan() retorna lista de dicts con info completa (ssid, rssi, channel, security, bssid) | Solo SSIDs, formato nativo (tuples) | Datos completos para portal de configuracion. Dicts por legibilidad. Dedup por SSID conservando mejor RSSI |
| 2026-02-11 | scan() retorna vacio si STA_IF no activo | Activar STA temporal, error | Explicito: el usuario debe activar STA primero. Sin efectos secundarios |
| 2026-02-11 | IP del AP configurable | Hardcoded 192.168.4.1 | Flexibilidad para diferentes topologias de red |
| 2026-02-11 | Debug mode con prefijo [WiFi Debug] | Sin debug | Consistente con Chess y ChessClock. Util para desarrollo |
| 2026-02-11 | Defaults auto-reconnect: 5s intervalo, 10 intentos | 10s/5, 3s/20 | Balance entre responsividad y consumo de recursos |
| 2026-02-11 | onReconnectFail desactiva STA_IF | Dejar activo sin conexion | Estado limpio: para reintentar se llama start() de nuevo |
| 2026-02-11 | sta.start() repetido reinicia conexion | No-op, retorna False | Permite cambiar de red WiFi sin stop() manual |
| 2026-02-11 | Reescribir tests completos | Adaptar existentes | Cambio de arquitectura demasiado grande para adaptar. Tests limpios desde cero |
| 2026-02-11 | Archivo unico WiFi.py | Archivos separados por sub-objeto | Menos archivos, imports simples, clases internas son privadas |
| 2026-02-11 | Testeable con mocks en CPython | Solo runtime MicroPython | Consistente con patron de AccessPoint actual. Permite CI |

---

## Observaciones y Decisiones Diferidas

- **Modulo MQTT**: Se especificara por separado. Dependera de `wifi.sta` para conectividad. La libreria MQTT (umqtt.simple, umqtt.robust o mqtt_as) se decidira en ese documento.
- **Portal web de configuracion**: Sera un modulo aparte que use `wifi.ap` para servir pagina de config y `wifi.sta` para aplicar credenciales WiFi y datos de broker MQTT.
- **Modulo SSE**: Queda obsoleto con la transicion a MQTT. Se eliminara cuando MQTT este implementado.
- **Persistencia de configuracion**: Guardar SSID/password entre reinicios (NVS, archivo JSON) queda fuera de alcance de este modulo. Sera responsabilidad del portal web o un modulo de config.

---

## Version
- Version del documento: 1.0
- Fecha: Febrero 2026
