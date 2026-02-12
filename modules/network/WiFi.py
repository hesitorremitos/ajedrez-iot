"""
WiFi Module for ESP32 (MicroPython)

Unified WiFi manager that controls AP and STA interfaces independently.
Provides sub-objects wifi.ap and wifi.sta for Access Point and Station
management respectively. Both can operate simultaneously.
"""

try:
    import network
except ImportError:
    network = None

try:
    import uasyncio
except ImportError:
    import asyncio as uasyncio

import time


class _Ap:
    """Access Point sub-object. Manages AP_IF interface."""

    def __init__(self, wifi):
        self._wifi = wifi
        self._nic = None
        self._ssid = ""
        self._ip = ""

    async def start(self, ssid, password=None, ip="192.168.4.1"):
        """
        Start the Access Point - async, waits for activation.

        Returns:
            bool: True if successful or already active, False on error
        """
        try:
            # Store config values always
            self._ssid = ssid
            self._ip = ip

            if self._nic is not None and self._nic.active():
                return True

            if self._nic is None:
                self._nic = network.WLAN(network.AP_IF)

            self._nic.active(True)

            # Wait for activation
            max_wait = 20
            while not self._nic.active() and max_wait > 0:
                await uasyncio.sleep_ms(50)
                max_wait -= 1

            if password is None or password == "":
                self._nic.config(essid=ssid, authmode=0)
            else:
                self._nic.config(essid=ssid, password=password, authmode=3)

            # Note: Do NOT call ifconfig() - MicroPython configures DHCP automatically
            # Calling ifconfig() can break DHCP for clients
            # The 'ip' parameter is stored for getStatus() only

            self._wifi._log("AP started: {} on {}".format(ssid, ip))
            return True

        except Exception:
            return False

    def stop(self):
        """
        Stop the Access Point.

        Returns:
            bool: True if successful or already stopped, False on error
        """
        try:
            if self._nic is None or not self._nic.active():
                return True

            self._nic.active(False)
            self._wifi._log("AP stopped")
            return True

        except Exception:
            return False

    def getStatus(self):
        """
        Get current AP status.

        Returns:
            dict: Status with keys: active, ssid, ip
        """
        if self._nic is not None and self._nic.active():
            return {"active": True, "ssid": self._ssid, "ip": self._ip}
        return {"active": False, "ssid": "", "ip": ""}


class _Sta:
    """Station sub-object. Manages STA_IF interface with auto-reconnect."""

    def __init__(self, wifi):
        self._wifi = wifi
        self._nic = None
        self._task = None
        self._ssid = ""
        self._password = None
        self._reconnectInterval = 5000
        self._maxReconnects = 10
        self.onConnect = None
        self.onDisconnect = None
        self.onReconnectFail = None

    async def start(
        self, ssid, password=None, reconnectInterval=5000, maxReconnects=10
    ):
        """
        Start connection to a WiFi network - async, waits for initial connection.

        Returns:
            bool: True if connection attempt started, False on error
        """
        if self._task is not None:
            await self.stop()

        try:
            self._ssid = ssid
            self._password = password
            self._reconnectInterval = reconnectInterval
            self._maxReconnects = maxReconnects

            if self._nic is None:
                self._nic = network.WLAN(network.STA_IF)

            self._nic.active(True)
            self._nic.connect(ssid, password if password else "")

            self._wifi._log("STA connecting to: {}".format(ssid))

            # Wait for initial connection (with timeout)
            timeout_ms = 10000
            start_time = time.ticks_ms()

            while not self._nic.isconnected():
                if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                    self._wifi._log("STA initial connection timeout")
                    break
                await uasyncio.sleep_ms(100)

            # Launch monitor task
            self._task = uasyncio.create_task(self._monitor())

            return True

        except Exception:
            return False

    async def stop(self):
        """
        Disconnect and cancel auto-reconnect task - async.

        Returns:
            bool: True if successful or already stopped, False on error
        """
        try:
            _hadTask = self._task is not None
            _hadNic = self._nic is not None and self._nic.active()

            if not _hadTask and not _hadNic:
                return True

            if self._task is not None:
                self._task.cancel()
                try:
                    await self._task
                except uasyncio.CancelledError:
                    pass
                self._task = None

            if self._nic is not None and self._nic.active():
                self._nic.active(False)

            self._wifi._log("STA stopped")
            return True

        except Exception:
            return False

    async def _monitor(self):
        """Internal async coroutine for connection monitoring and
        auto-reconnect."""
        _wasConnected = False
        _reconnectCount = 0

        try:
            while True:
                await uasyncio.sleep_ms(self._reconnectInterval)

                if self._nic.isconnected():
                    if not _wasConnected:
                        _wasConnected = True
                        _reconnectCount = 0
                        ip = self._nic.ifconfig()[0]
                        if self.onConnect:
                            self.onConnect(ip)
                        self._wifi._log("STA connected, IP: {}".format(ip))
                else:
                    if _wasConnected:
                        _wasConnected = False
                        if self.onDisconnect:
                            self.onDisconnect()
                        self._wifi._log("STA disconnected")

                    _reconnectCount += 1
                    self._wifi._log(
                        "STA reconnect attempt {} of {}".format(
                            _reconnectCount, self._maxReconnects
                        )
                    )

                    if _reconnectCount >= self._maxReconnects:
                        self._wifi._log(
                            "STA reconnect failed after {} attempts".format(
                                self._maxReconnects
                            )
                        )
                        if self.onReconnectFail:
                            self.onReconnectFail()
                        self._nic.active(False)
                        self._task = None
                        return

                    try:
                        if self._password:
                            self._nic.connect(self._ssid, self._password)
                        else:
                            self._nic.connect(self._ssid)
                    except Exception:
                        pass

        except uasyncio.CancelledError:
            pass

    def isConnected(self):
        """
        Check if STA is connected to a WiFi network.

        Returns:
            bool: True if connected, False otherwise
        """
        if self._nic is None:
            return False
        return self._nic.isconnected()

    def getStatus(self):
        """
        Get current STA status.

        Returns:
            dict: Status with keys: connected, ssid, ip
        """
        if self._nic is not None and self._nic.isconnected():
            return {
                "connected": True,
                "ssid": self._ssid,
                "ip": self._nic.ifconfig()[0],
            }
        return {"connected": False, "ssid": "", "ip": ""}

    async def scan(self):
        """
        Scan for available WiFi networks - async, activates STA automatically if needed.

        Returns:
            list: List of dicts with ssid, rssi, channel, security, bssid.
                  Empty list on error.
        """
        try:
            # Activate STA if not active
            was_active = self._nic is not None and self._nic.active()
            if not was_active:
                if self._nic is None:
                    self._nic = network.WLAN(network.STA_IF)
                self._nic.active(True)
                # Small delay for interface to initialize
                await uasyncio.sleep_ms(100)

            # Temporarily disable AP for better scan results (ESP32 limitation)
            ap_was_active = False
            if self._wifi.ap._nic is not None and self._wifi.ap._nic.active():
                ap_was_active = True
                self._wifi.ap._nic.active(False)
                await uasyncio.sleep_ms(50)

            try:
                self._wifi._log("STA scanning...")
                results = self._nic.scan()

                # Re-enable AP if it was active
                if ap_was_active:
                    self._wifi.ap._nic.active(True)

                best = {}

                for entry in results:
                    ssid_bytes, bssid_bytes, channel, rssi, security, hidden = entry

                    if hidden != 0:
                        continue

                    ssid = (
                        ssid_bytes.decode("utf-8")
                        if isinstance(ssid_bytes, bytes)
                        else str(ssid_bytes)
                    )

                    if not ssid:
                        continue

                    if ssid not in best or rssi > best[ssid]["rssi"]:
                        bssid = ":".join("{:02x}".format(b) for b in bssid_bytes)
                        best[ssid] = {
                            "ssid": ssid,
                            "rssi": rssi,
                            "channel": channel,
                            "security": security,
                            "bssid": bssid,
                        }

                networks = list(best.values())
                self._wifi._log("STA scan: {} networks found".format(len(networks)))
                return networks

            except Exception:
                if ap_was_active:
                    self._wifi.ap._nic.active(True)
                return []

        except Exception:
            return []


class WiFi:
    """
    Unified WiFi manager for ESP32.

    Provides independent AP and STA sub-objects for managing
    both interfaces simultaneously.
    """

    def __init__(self, debug=False):
        self._debug = debug
        self.ap = _Ap(self)
        self.sta = _Sta(self)

    def _log(self, msg):
        """Print debug message if debug mode is enabled."""
        if self._debug:
            print("[WiFi Debug] {}".format(msg))
