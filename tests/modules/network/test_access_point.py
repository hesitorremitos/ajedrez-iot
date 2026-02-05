"""
Tests for AccessPoint module

All tests use mocks to simulate MicroPython's network.WLAN interface.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys


class MockWLAN:
    """Mock for network.WLAN class"""

    def __init__(self, interface_type):
        self.interface_type = interface_type
        self._active = False
        self._config = {}
        self._stations = []

    def active(self, state=None):
        if state is None:
            return self._active
        self._active = state

    def config(self, **kwargs):
        self._config.update(kwargs)

    def status(self, param=None):
        if param == "stations":
            return self._stations
        return None

    def set_stations(self, stations):
        """Test helper to set connected stations"""
        self._stations = stations


@pytest.fixture
def mock_network():
    """Create mock network module with AP_IF and STA_IF constants"""
    mock_net = MagicMock()
    mock_net.AP_IF = 1
    mock_net.STA_IF = 0

    # Store WLAN instances to track state
    mock_net._ap_instance = None
    mock_net._sta_instance = None

    def create_wlan(interface_type):
        if interface_type == mock_net.AP_IF:
            if mock_net._ap_instance is None:
                mock_net._ap_instance = MockWLAN(interface_type)
            return mock_net._ap_instance
        else:
            if mock_net._sta_instance is None:
                mock_net._sta_instance = MockWLAN(interface_type)
            return mock_net._sta_instance

    mock_net.WLAN = create_wlan

    return mock_net


@pytest.fixture
def access_point_module(mock_network):
    """Import AccessPoint with mocked network module"""
    # Patch network module before importing
    with patch.dict(sys.modules, {"network": mock_network}):
        # Remove cached module if exists
        if "modules.network.AccessPoint" in sys.modules:
            del sys.modules["modules.network.AccessPoint"]
        if "modules.network" in sys.modules:
            del sys.modules["modules.network"]

        # Import with mock
        import importlib

        spec = importlib.util.spec_from_file_location(
            "AccessPoint", "modules/network/AccessPoint.py"
        )
        module = importlib.util.module_from_spec(spec)

        # Inject mocked network
        module.network = mock_network
        spec.loader.exec_module(module)

        yield module, mock_network


class TestAccessPointCreation:
    """Tests for AC-01 and AC-02: Instance creation"""

    def test_ac01_create_with_ssid_and_password(self, access_point_module):
        """AC-01: Create instance with SSID and password"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")

        assert ap._ssid == "Test"
        assert ap._password == "12345678"

    def test_ac02_create_without_password_open_network(self, access_point_module):
        """AC-02: Create instance without password (open AP)"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test")

        assert ap._ssid == "Test"
        assert ap._password is None


class TestAccessPointStart:
    """Tests for AC-03, AC-04, AC-13, AC-14, AC-15: start() method"""

    def test_ac03_start_initiates_ap_correctly(self, access_point_module):
        """AC-03: start() initiates AP correctly"""
        AccessPoint, mock_net = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        result = ap.start()

        assert result is True
        assert ap._ap.active() is True
        assert ap._ap._config["essid"] == "Test"
        assert ap._ap._config["password"] == "12345678"
        assert ap._ap._config["authmode"] == 3  # WPA2-PSK

    def test_ac04_start_when_already_active_returns_true(self, access_point_module):
        """AC-04: start() when already active returns True without action"""
        AccessPoint, mock_net = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        # Modify config to detect if start() does anything
        original_config = dict(ap._ap._config)

        result = ap.start()

        assert result is True
        assert ap._ap._config == original_config  # Config unchanged

    def test_ac13_start_deactivates_sta_if(self, access_point_module):
        """AC-13: start() deactivates STA_IF"""
        AccessPoint, mock_net = access_point_module

        # Pre-activate STA
        sta = mock_net.WLAN(mock_net.STA_IF)
        sta.active(True)

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        assert sta.active() is False  # STA was deactivated

    def test_ac14_start_returns_false_on_error(self, access_point_module):
        """AC-14: start() returns False on error"""
        AccessPoint, mock_net = access_point_module

        # Make WLAN raise exception
        def raise_error(interface):
            raise Exception("Hardware not available")

        mock_net.WLAN = raise_error

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        result = ap.start()

        assert result is False

    def test_ac15_open_network_with_empty_password(self, access_point_module):
        """AC-15: AP with empty password creates open network"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Open", password="")
        result = ap.start()

        assert result is True
        assert ap._ap._config["authmode"] == 0  # Open network
        assert "password" not in ap._ap._config


class TestAccessPointStop:
    """Tests for AC-05, AC-06: stop() method"""

    def test_ac05_stop_deactivates_ap(self, access_point_module):
        """AC-05: stop() deactivates AP correctly"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        result = ap.stop()

        assert result is True
        assert ap._ap.active() is False

    def test_ac06_stop_when_already_stopped_returns_true(self, access_point_module):
        """AC-06: stop() when already stopped returns True"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        # Never started, so already stopped

        result = ap.stop()

        assert result is True

    def test_stop_after_stop_returns_true(self, access_point_module):
        """Calling stop() twice returns True"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()
        ap.stop()

        result = ap.stop()

        assert result is True


class TestAccessPointConfigure:
    """Tests for AC-07, AC-08, AC-09: configure() method"""

    def test_ac07_configure_updates_params_when_stopped(self, access_point_module):
        """AC-07: configure() updates parameters with AP stopped"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Old", password="12345678")

        result = ap.configure(ssid="New")

        assert result is True
        assert ap._ssid == "New"
        assert ap._ap is None  # AP was never started

    def test_ac08_configure_applies_immediately_when_active(self, access_point_module):
        """AC-08: configure() applies changes immediately when AP active"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Old", password="12345678")
        ap.start()

        result = ap.configure(ssid="New")

        assert result is True
        assert ap._ssid == "New"
        assert ap._ap.active() is True  # AP still active
        assert ap._ap._config["essid"] == "New"

    def test_ac09_configure_only_updates_provided_params(self, access_point_module):
        """AC-09: configure() only updates provided parameters"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")

        ap.configure(ssid="Nuevo")

        assert ap._ssid == "Nuevo"
        assert ap._password == "12345678"  # Unchanged

    def test_configure_password_only(self, access_point_module):
        """configure() can update only password"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="oldpass")

        ap.configure(password="newpass")

        assert ap._ssid == "Test"  # Unchanged
        assert ap._password == "newpass"


class TestAccessPointGetStatus:
    """Tests for AC-10, AC-11: getStatus() method"""

    def test_ac10_get_status_returns_correct_format_when_active(
        self, access_point_module
    ):
        """AC-10: getStatus() returns correct format when active"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        status = ap.getStatus()

        assert status["active"] is True
        assert status["ssid"] == "Test"
        assert status["ip"] == "192.168.4.1"
        assert "clientCount" in status
        assert isinstance(status["clientCount"], int)

    def test_ac11_get_status_when_stopped(self, access_point_module):
        """AC-11: getStatus() with AP stopped"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        # Never started

        status = ap.getStatus()

        assert status["active"] is False
        assert status["ssid"] == "Test"
        assert status["clientCount"] == 0

    def test_get_status_with_clients(self, access_point_module):
        """getStatus() returns correct client count"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        # Simulate 2 connected clients
        ap._ap.set_stations(
            [(b"\xaa\xbb\xcc\xdd\xee\xff",), (b"\x11\x22\x33\x44\x55\x66",)]
        )

        status = ap.getStatus()

        assert status["clientCount"] == 2


class TestAccessPointGetClients:
    """Tests for AC-12: getClients() method"""

    def test_ac12_get_clients_returns_native_format(self, access_point_module):
        """AC-12: getClients() returns native MicroPython format"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        # Simulate connected clients in native format
        native_clients = [
            (b"\xaa\xbb\xcc\xdd\xee\xff",),
            (b"\x11\x22\x33\x44\x55\x66",),
        ]
        ap._ap.set_stations(native_clients)

        clients = ap.getClients()

        assert clients == native_clients

    def test_get_clients_when_stopped_returns_empty(self, access_point_module):
        """getClients() returns empty list when AP stopped"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        # Never started

        clients = ap.getClients()

        assert clients == []

    def test_get_clients_no_clients_returns_empty(self, access_point_module):
        """getClients() returns empty list when no clients"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        clients = ap.getClients()

        assert clients == []


class TestAccessPointOpenNetwork:
    """Tests for open network (no password) scenarios"""

    def test_open_network_with_none_password(self, access_point_module):
        """AP with None password creates open network"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Open")
        ap.start()

        assert ap._ap._config["authmode"] == 0

    def test_open_network_with_empty_string_password(self, access_point_module):
        """AP with empty string password creates open network"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Open", password="")
        ap.start()

        assert ap._ap._config["authmode"] == 0


class TestAccessPointErrorHandling:
    """Tests for error handling scenarios"""

    def test_start_handles_exception_gracefully(self, access_point_module):
        """start() catches exceptions and returns False"""
        AccessPoint, mock_net = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")

        # Make active() raise exception
        original_wlan = mock_net.WLAN

        def failing_wlan(interface):
            raise RuntimeError("WiFi hardware error")

        mock_net.WLAN = failing_wlan

        result = ap.start()

        assert result is False

    def test_stop_handles_exception_gracefully(self, access_point_module):
        """stop() catches exceptions and returns False"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        # Make active() raise exception on next call
        def raise_error(state=None):
            raise RuntimeError("WiFi error")

        ap._ap.active = raise_error

        result = ap.stop()

        assert result is False

    def test_configure_handles_restart_failure(self, access_point_module):
        """configure() returns False if restart fails"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        # Make AP config fail on restart by making active() raise on specific call
        original_active = ap._ap.active
        call_count = [0]

        def failing_active(state=None):
            call_count[0] += 1
            # First two calls: check active (True), deactivate (stop)
            # Third call onwards: fail (simulate hardware error on restart)
            if call_count[0] >= 3 and state is True:
                raise RuntimeError("Cannot restart AP")
            return original_active(state)

        ap._ap.active = failing_active

        result = ap.configure(ssid="New")

        # Should return False because start failed during restart
        assert result is False


class TestAccessPointIdempotency:
    """Tests for idempotent behavior"""

    def test_multiple_start_calls_safe(self, access_point_module):
        """Multiple start() calls are safe"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")

        assert ap.start() is True
        assert ap.start() is True
        assert ap.start() is True
        assert ap._ap.active() is True

    def test_multiple_stop_calls_safe(self, access_point_module):
        """Multiple stop() calls are safe"""
        AccessPoint, _ = access_point_module

        ap = AccessPoint.AccessPoint(ssid="Test", password="12345678")
        ap.start()

        assert ap.stop() is True
        assert ap.stop() is True
        assert ap.stop() is True
