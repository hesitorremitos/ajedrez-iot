---
last_updated: "2026-02-05 12:00"
version: "1.0"
status: draft
author: Discovery Architect
---

# AccessPoint Module - Documento de Requerimientos

## Descripcion General

Desarrollar un modulo de Access Point WiFi llamado `AccessPoint.py` para ESP32 (MicroPython) que permita al microcontrolador crear una red WiFi propia (modo AP). Los dispositivos se conectan al AP para comunicarse directamente con el ESP32. El modulo es de uso general; uno de los casos de uso previstos es permitir que jugadores se conecten para partidas de ajedrez via un futuro modulo WebSocket.

Este modulo maneja **exclusivamente la capa de red AP**. La mensajeria (WebSocket, HTTP, etc.) sera responsabilidad de modulos separados.

## Restricciones Tecnicas

- Compatible con MicroPython para ESP32
- Usar camelCase para todos los nombres de metodos y propiedades
- Ubicacion del archivo: `modules/network/AccessPoint.py`
- Nombre de la clase: `AccessPoint`
- Sin modo debug (a diferencia del modulo Chess)
- Sin captive portal
- Sin servidor web/HTTP integrado
- Sin persistencia de configuracion entre reinicios del ESP32

---

## API Publica

### Constructor

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `ssid` | `str` | (requerido) | Nombre de la red WiFi del AP |
| `password` | `str \| None` | `None` | Password del AP. Si es `None` o `''`, el AP es abierto (sin autenticacion) |

```python
ap = AccessPoint(ssid='Zulma', password='12345678')
```

### Metodos de Control

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `start` | ninguno | `bool` | Inicia el AP. Retorna `True` si exitoso, `False` si fallo. Si ya esta activo, retorna `True` sin hacer nada. Al iniciar, desactiva STA_IF para evitar conflictos |
| `stop` | ninguno | `bool` | Detiene el AP. Retorna `True` si exitoso, `False` si fallo. Si ya esta detenido, retorna `True` sin hacer nada |
| `configure` | `ssid: str = None`, `password: str = None` | `bool` | Actualiza parametros de configuracion. Solo actualiza los parametros proporcionados (no-None). Si el AP esta activo, aplica cambios inmediatamente (stop + start automatico). Retorna `True` si exitoso |

### Metodos de Consulta

| Metodo | Parametros | Retorno | Descripcion |
|--------|------------|---------|-------------|
| `getStatus` | ninguno | `dict` | Retorna estado actual del AP (ver formato abajo) |
| `getClients` | ninguno | `list` | Retorna lista de clientes conectados en formato nativo de MicroPython |

---

## Formatos de Retorno

### getStatus()

Retorna un diccionario con los siguientes campos:

```python
{
    'active': True,        # bool - si el AP esta activo
    'ssid': 'Zulma',       # str - nombre de la red
    'ip': '192.168.4.1',   # str - direccion IP del AP
    'clientCount': 2       # int - numero de clientes conectados
}
```

### getClients()

Retorna la lista en el formato nativo de MicroPython (`network.WLAN.status('stations')`), sin transformacion. El formato tipico es una lista de tuples con informacion de cada estacion conectada.

```python
# Formato nativo tipico (puede variar segun firmware):
[(b'\xaa\xbb\xcc\xdd\xee\xff', ...)]
```

---

## Configuracion de Red

### Valores Fijos (no configurables)

| Parametro | Valor |
|-----------|-------|
| IP del AP | `192.168.4.1` |
| Mascara de subred | `255.255.255.0` |
| Gateway | `192.168.4.1` |
| Canal WiFi | Default de MicroPython |
| Max clientes | Default del ESP32 |

### Autenticacion

- El tipo de autenticacion WiFi sera el que soporte MicroPython por defecto (tipicamente WPA2-PSK)
- Si `password` es `None` o string vacio `''`, el AP se crea como red abierta (sin autenticacion)
- No se realiza validacion de parametros (longitud de password, caracteres de SSID, etc.). Se pasan directamente a MicroPython

---

## Comportamiento Detallado

### start()

1. Desactiva `network.STA_IF` si esta activo (evitar conflictos AP+STA)
2. Activa `network.AP_IF`
3. Configura SSID, password y modo de autenticacion
4. Si el AP ya esta activo al momento de llamar, retorna `True` sin hacer nada
5. Retorna `True` si el AP se inicio correctamente, `False` en caso de error

### stop()

1. Desactiva `network.AP_IF`
2. Si el AP ya esta detenido al momento de llamar, retorna `True` sin hacer nada
3. Retorna `True` si se detuvo correctamente, `False` en caso de error

### configure()

1. Acepta parametros opcionales: `ssid`, `password`
2. Solo actualiza los parametros que se proporcionan (los que no son `None`)
3. Almacena los nuevos valores internamente
4. Si el AP esta activo al momento de llamar:
   - Ejecuta `stop()` automaticamente
   - Ejecuta `start()` con la nueva configuracion
5. Si el AP esta detenido, solo guarda los valores para el proximo `start()`
6. Retorna `True` si exitoso, `False` si fallo (ej: el restart automatico fallo)

### Coexistencia AP/STA

- Al llamar `start()`, el modulo **desactiva STA_IF** automaticamente
- Esto es una decision de diseño para evitar conflictos de red
- Si en el futuro se necesita modo AP+STA simultaneo, sera un cambio de alcance

---

## Manejo de Errores

- **Sin excepciones custom**: el modulo usa return codes (`True`/`False`)
- **Sin validacion de parametros**: los valores se pasan directamente a la API de MicroPython `network.WLAN`
- Si MicroPython lanza una excepcion interna (ej: hardware no disponible), el modulo la captura y retorna `False`

---

## Funcionalidad Excluida (fuera de alcance)

- Captive portal
- Servidor web/HTTP
- WebSocket (sera modulo separado)
- Callbacks de conexion/desconexion de clientes (no hay mecanismo nativo eficiente)
- Modo debug
- Persistencia de configuracion entre reinicios
- Configuracion de canal WiFi
- Configuracion de IP/mascara/gateway
- Validacion de parametros de entrada
- Modo AP+STA simultaneo

---

## Estructura de Archivos

```
modules/
  network/
    __init__.py          # Exporta AccessPoint
    AccessPoint.py       # Clase principal
tests/
  modules/
    network/
      test_access_point.py  # Tests con mocks
```

---

## Ejemplo de Uso Esperado

```python
from modules.network import AccessPoint

# Crear AP con password
ap = AccessPoint(ssid='Zulma', password='12345678')
ap.start()          # True

# Consultar estado
ap.getStatus()      # {'active': True, 'ssid': 'Zulma', 'ip': '192.168.4.1', 'clientCount': 0}
ap.getClients()     # []

# Reconfigurar (aplica inmediatamente si esta activo)
ap.configure(ssid='Zulma-v2')  # True (hace stop+start internamente)

# Detener
ap.stop()           # True

# Crear AP abierto (sin password)
ap_open = AccessPoint(ssid='Zulma-Open')
ap_open.start()     # True - red abierta

# Llamar start cuando ya esta activo
ap_open.start()     # True - no hace nada, ya esta activo

# Llamar stop cuando ya esta detenido
ap_open.stop()      # True
ap_open.stop()      # True - no hace nada, ya esta detenido
```

---

## Criterios de Aceptacion

### Tests Automatizados (con mocks de `network.WLAN`)

#### AC-01: Crear instancia con SSID y password
- **Given** parametros ssid='Test' y password='12345678'
- **When** se crea `AccessPoint(ssid='Test', password='12345678')`
- **Then** la instancia se crea sin errores y almacena los parametros internamente

#### AC-02: Crear instancia sin password (AP abierto)
- **Given** parametro ssid='Test' sin password
- **When** se crea `AccessPoint(ssid='Test')`
- **Then** la instancia se crea con password=None (red abierta)

#### AC-03: start() inicia el AP correctamente
- **Given** una instancia de AccessPoint no iniciada
- **When** se llama `start()`
- **Then** retorna `True`, desactiva STA_IF, activa AP_IF con SSID y password configurados

#### AC-04: start() cuando ya esta activo retorna True sin accion
- **Given** un AP ya iniciado
- **When** se llama `start()` nuevamente
- **Then** retorna `True` sin reiniciar el AP

#### AC-05: stop() detiene el AP correctamente
- **Given** un AP activo
- **When** se llama `stop()`
- **Then** retorna `True` y desactiva AP_IF

#### AC-06: stop() cuando ya esta detenido retorna True sin accion
- **Given** un AP ya detenido
- **When** se llama `stop()` nuevamente
- **Then** retorna `True` sin hacer nada

#### AC-07: configure() actualiza parametros con AP detenido
- **Given** un AP detenido con ssid='Old'
- **When** se llama `configure(ssid='New')`
- **Then** retorna `True`, el SSID interno se actualiza a 'New', el AP NO se inicia

#### AC-08: configure() aplica cambios inmediatamente con AP activo
- **Given** un AP activo con ssid='Old'
- **When** se llama `configure(ssid='New')`
- **Then** retorna `True`, ejecuta stop+start internamente, el AP queda activo con ssid='New'

#### AC-09: configure() solo actualiza parametros proporcionados
- **Given** un AP con ssid='Test' y password='12345678'
- **When** se llama `configure(ssid='Nuevo')` (sin password)
- **Then** el SSID cambia a 'Nuevo', el password se mantiene en '12345678'

#### AC-10: getStatus() retorna estado correcto
- **Given** un AP activo con ssid='Test'
- **When** se llama `getStatus()`
- **Then** retorna dict con keys: `active` (True), `ssid` ('Test'), `ip` ('192.168.4.1'), `clientCount` (int)

#### AC-11: getStatus() con AP detenido
- **Given** un AP detenido
- **When** se llama `getStatus()`
- **Then** retorna dict con `active: False` y valores coherentes

#### AC-12: getClients() retorna formato nativo
- **Given** un AP activo con clientes conectados
- **When** se llama `getClients()`
- **Then** retorna la lista en formato nativo de MicroPython sin transformacion

#### AC-13: start() desactiva STA_IF
- **Given** STA_IF esta activo
- **When** se llama `start()` en el AP
- **Then** STA_IF se desactiva antes de activar AP_IF

#### AC-14: start() retorna False en caso de error
- **Given** el hardware WiFi no esta disponible (mock lanza excepcion)
- **When** se llama `start()`
- **Then** retorna `False` sin propagar la excepcion

#### AC-15: AP abierto con password vacio
- **Given** AccessPoint(ssid='Open', password='')
- **When** se llama `start()`
- **Then** el AP se crea sin autenticacion (red abierta)

---

## Decisions Log

| Fecha | Decision | Alternativas Consideradas | Razon |
|-------|----------|---------------------------|-------|
| 2026-02-05 | Solo capa AP, sin servidor web | AP + servidor web, AP + WebSocket | Separacion de responsabilidades; WebSocket sera modulo aparte |
| 2026-02-05 | Sin callbacks onConnect/onDisconnect | Polling periodico, timer interno, metodo manual check | MicroPython no tiene eventos nativos eficientes para deteccion de clientes |
| 2026-02-05 | Return codes en lugar de excepciones | Excepciones custom, callback onError, excepciones + callback | Consistencia con patron de Chess.play() que retorna bool |
| 2026-02-05 | Desactivar STA_IF al iniciar AP | Ignorar STA, coexistencia AP+STA | Evitar conflictos de red; si se necesita AP+STA sera cambio de alcance |
| 2026-02-05 | configure() aplica cambios inmediatamente si AP activo | Guardar y esperar restart manual, error si activo | Mejor UX: el usuario no necesita recordar hacer stop+start |
| 2026-02-05 | Sin validacion de parametros | Validacion completa, validacion minima | Delegar a MicroPython; reduce complejidad y tamaño del modulo |
| 2026-02-05 | getClients() retorna formato nativo | Lista de dicts, lista de tuples custom | Optimiza memoria al no transformar datos |
| 2026-02-05 | Sin persistencia de configuracion | Archivo JSON, NVS | Se configura desde codigo en cada arranque; simplicidad |
| 2026-02-05 | Sin modo debug | Debug como en Chess | No necesario para este modulo segun requerimiento del usuario |

---

## Observaciones y Decisiones Diferidas

_No hay decisiones diferidas. Todos los puntos fueron resueltos durante la entrevista._

---

## Version
- Version del documento: 1.0
- Fecha: Febrero 2026
