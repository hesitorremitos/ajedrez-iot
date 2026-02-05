"""
AccessPoint Module for ESP32 (MicroPython)

Creates a WiFi Access Point allowing devices to connect directly to the ESP32.
This module handles exclusively the AP network layer.
"""

try:
    import network
except ImportError:
    # For testing environments without MicroPython
    network = None


class AccessPoint:
    """
    WiFi Access Point manager for ESP32.

    Creates and manages a WiFi AP allowing devices to connect
    directly to the microcontroller.
    """

    # Fixed network configuration
    _AP_IP = "192.168.4.1"
    _AP_SUBNET = "255.255.255.0"
    _AP_GATEWAY = "192.168.4.1"

    def __init__(self, ssid, password=None):
        """
        Initialize AccessPoint instance.

        Args:
            ssid: Name of the WiFi network (required)
            password: AP password. If None or '', creates an open network
        """
        self._ssid = ssid
        self._password = password
        self._ap = None
        self._sta = None

    def start(self):
        """
        Start the Access Point.

        Deactivates STA_IF to avoid conflicts, then activates AP_IF
        with the configured SSID and password.

        Returns:
            bool: True if successful or already active, False on error
        """
        try:
            # Initialize interfaces if needed
            if self._ap is None:
                self._ap = network.WLAN(network.AP_IF)
            if self._sta is None:
                self._sta = network.WLAN(network.STA_IF)

            # If already active, return True without doing anything
            if self._ap.active():
                return True

            # Deactivate STA_IF to avoid conflicts
            if self._sta.active():
                self._sta.active(False)

            # Activate AP_IF
            self._ap.active(True)

            # Configure AP with SSID and authentication
            if self._password is None or self._password == "":
                # Open network (no authentication)
                self._ap.config(essid=self._ssid, authmode=0)
            else:
                # WPA2-PSK authentication (authmode=3)
                self._ap.config(essid=self._ssid, password=self._password, authmode=3)

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
            # If not initialized or already inactive, return True
            if self._ap is None:
                return True

            if not self._ap.active():
                return True

            # Deactivate AP_IF
            self._ap.active(False)
            return True

        except Exception:
            return False

    def configure(self, ssid=None, password=None):
        """
        Update AP configuration parameters.

        Only updates parameters that are provided (not None).
        If the AP is active, applies changes immediately (stop + start).

        Args:
            ssid: New SSID (optional)
            password: New password (optional)

        Returns:
            bool: True if successful, False on error
        """
        try:
            # Update only provided parameters
            if ssid is not None:
                self._ssid = ssid
            if password is not None:
                self._password = password

            # If AP is active, restart to apply changes
            wasActive = self._ap is not None and self._ap.active()

            if wasActive:
                if not self.stop():
                    return False
                if not self.start():
                    return False

            return True

        except Exception:
            return False

    def getStatus(self):
        """
        Get current AP status.

        Returns:
            dict: Status with keys: active, ssid, ip, clientCount
        """
        try:
            isActive = self._ap is not None and self._ap.active()

            if isActive:
                # Get client count from stations
                try:
                    clients = self._ap.status("stations")
                    clientCount = len(clients) if clients else 0
                except Exception:
                    clientCount = 0

                return {
                    "active": True,
                    "ssid": self._ssid,
                    "ip": self._AP_IP,
                    "clientCount": clientCount,
                }
            else:
                return {"active": False, "ssid": self._ssid, "ip": "", "clientCount": 0}

        except Exception:
            return {"active": False, "ssid": self._ssid, "ip": "", "clientCount": 0}

    def getClients(self):
        """
        Get list of connected clients.

        Returns:
            list: Native MicroPython format from WLAN.status('stations')
        """
        try:
            if self._ap is None or not self._ap.active():
                return []

            clients = self._ap.status("stations")
            return clients if clients else []

        except Exception:
            return []

    def getClientsInfo(self):
        """
        Get list of connected clients with formatted information.

        Returns:
            list: List of dicts with client info. Each dict contains:
                  {'mac': 'aa:bb:cc:dd:ee:ff'}

        Note: IP addresses are not available in MicroPython's AP mode
              without implementing a full DHCP server.
        """
        try:
            clients = self.getClients()
            if not clients:
                return []

            formatted = []
            for client in clients:
                # client[0] contains MAC address as bytes
                mac_bytes = client[0]
                mac_str = ":".join(f"{b:02x}" for b in mac_bytes)
                formatted.append({"mac": mac_str})

            return formatted

        except Exception:
            return []
