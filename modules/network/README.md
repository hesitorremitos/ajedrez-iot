# AccessPoint Module

Módulo WiFi Access Point para ESP32 (MicroPython).

## Instalación

```bash
# Copiar a tu ESP32
ampy --port COM3 put modules/network /modules/network
```

## Uso

### Crear y iniciar AP

```python
from modules.network import AccessPoint

# Con password
ap = AccessPoint(ssid='MiRed', password='12345678')
ap.start()

# Sin password (red abierta)
ap = AccessPoint(ssid='RedAbierta')
ap.start()
```

```

### Consultar estado

```python
status = ap.getStatus()
print(status)
# {'active': True, 'ssid': 'MiRed', 'ip': '192.168.4.1', 'clientCount': 0}
```

### Ver clientes conectados

```python
# Formato nativo (bytes)
clients = ap.getClients()
print(f"Clientes: {len(clients)}")

# Formato legible (recomendado)
clients_info = ap.getClientsInfo()
for client in clients_info:
    print(f"MAC: {client['mac']}")
# Output: MAC: aa:bb:cc:dd:ee:ff
```

### Cambiar configuración

```python
# Cambia SSID y/o password (reinicia automáticamente si está activo)
ap.configure(ssid='NuevoNombre')
ap.configure(password='newpass')
ap.configure(ssid='Otro', password='pass123')
```

### Detener AP

```python
ap.stop()
```

---

## API

### `AccessPoint(ssid, password=None)`

Crea instancia del AP.

- `ssid`: Nombre de la red (requerido)
- `password`: Contraseña. Si es `None` o `''`, red abierta

### `start() -> bool`

Inicia el AP. Retorna `True` si exitoso.

### `stop() -> bool`

Detiene el AP. Retorna `True` si exitoso.

### `configure(ssid=None, password=None) -> bool`

Actualiza configuración. Solo actualiza parámetros no-None.
Si AP está activo, reinicia automáticamente.

### `getStatus() -> dict`

Retorna:
```python
{
    'active': bool,      # Si el AP está activo
    'ssid': str,         # Nombre de la red
    'ip': str,           # IP del AP (siempre 192.168.4.1)
    'clientCount': int   # Clientes conectados
}
```

### `getClients() -> list`

Retorna lista de clientes en formato nativo MicroPython (bytes crudos).

### `getClientsInfo() -> list`

Retorna lista de clientes con formato legible.

**Retorna:**
```python
[
    {'mac': 'aa:bb:cc:dd:ee:ff'},
    {'mac': '11:22:33:44:55:66'}
]
```

**Nota:** Las IPs de los clientes no están disponibles en MicroPython sin implementar un servidor DHCP completo.

---

## Ejemplos

### Ejemplo 1: AP básico

```python
from modules.network import AccessPoint
import time

ap = AccessPoint(ssid='ESP32', password='12345678')

if ap.start():
    print("AP activo en 192.168.4.1")
    
    while True:
        status = ap.getStatus()
        print(f"Clientes: {status['clientCount']}")
        time.sleep(5)
```

### Ejemplo 2: Ver clientes conectados

```python
from modules.network import AccessPoint
import time

ap = AccessPoint(ssid='Monitor', password='test1234')
ap.start()

while True:
    clients = ap.getClientsInfo()
    
    if clients:
        print(f"\n{len(clients)} clientes conectados:")
        for i, client in enumerate(clients):
            print(f"  {i+1}. MAC: {client['mac']}")
    else:
        print("Sin clientes")
    
    time.sleep(5)
```

### Ejemplo 3: Red temporal

```python
from modules.network import AccessPoint
import time

ap = AccessPoint(ssid='Temporal', password='temp123')
ap.start()
print("AP activo por 60 segundos")

time.sleep(60)

ap.stop()
print("AP detenido")
```

---

## Configuración Fija

| Parámetro | Valor |
|-----------|-------|
| IP | `192.168.4.1` |
| Máscara | `255.255.255.0` |
| Gateway | `192.168.4.1` |
| Autenticación | WPA2-PSK (con password) / Open (sin password) |

---

## Notas

- Al llamar `start()`, se desactiva automáticamente `STA_IF`
- No valida parámetros (SSID/password)
- Sin persistencia entre reinicios
- Métodos retornan `True`/`False` (sin excepciones)
