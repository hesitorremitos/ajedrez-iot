"""
Tests for WiFi module

All tests use mocks to simulate MicroPython's network.WLAN and uasyncio.
Covers AP sub-object, STA sub-object, independence, callbacks, and debug mode.
"""

import asyncio
import importlib
import importlib.util
import sys

import pytest
from unittest.mock import MagicMock, patch


class MockWLAN:
    """Mock for network.WLAN class"""

    def __init__(self, interface_type):
        self.interface_type = interface_type
        self._active = False
        self._connected = False
        self._config = {}
        self._ifconfig = ("0.0.0.0", "255.255.255.0", "0.0.0.0", "0.0.0.0")
        self._scan_results = []
        self._connectCalls = []

    def active(self, state=None):
        if state is None:
            return self._active
        self._active = state

    def config(self, **kwargs):
        self._config.update(kwargs)

    def ifconfig(self, config=None):
        if config is not None:
            self._ifconfig = config
        return self._ifconfig

    def connect(self, *args):
        self._connectCalls.append(args)

    def isconnected(self):
        return self._connected

    def scan(self):
        return self._scan_results


class MockTask:
    """Lightweight awaitable task-like object for tests."""

    def __init__(self):
        self.cancelCalled = 0
        self._cancelled = False

    def cancel(self):
        self.cancelCalled += 1
        self._cancelled = True

    def __await__(self):
        async def _wait():
            if self._cancelled:
                raise asyncio.CancelledError()
            return None

        return _wait().__await__()


@pytest.fixture
def mock_network():
    """Create mock network module with AP_IF and STA_IF constants"""
    mock_net = MagicMock()
    mock_net.AP_IF = 1
    mock_net.STA_IF = 0

    _instances = {}

    def create_wlan(interface_type):
        if interface_type not in _instances:
            _instances[interface_type] = MockWLAN(interface_type)
        return _instances[interface_type]

    mock_net.WLAN = create_wlan
    return mock_net


@pytest.fixture
def mock_time():
    """Create mock time module with ticks_ms and ticks_diff"""
    mock_t = MagicMock()
    _tick_counter = [0]

    def ticks_ms():
        _tick_counter[0] += 100
        return _tick_counter[0]

    def ticks_diff(end, start):
        return end - start

    mock_t.ticks_ms = ticks_ms
    mock_t.ticks_diff = ticks_diff
    return mock_t


@pytest.fixture
def wifi_module(mock_network, mock_time):
    """Import WiFi with mocked network, time, and uasyncio"""
    mock_uasyncio = MagicMock()

    def create_task(coro):
        coro.close()
        return MockTask()

    mock_uasyncio.create_task = MagicMock(side_effect=create_task)

    async def mock_sleep_ms(ms):
        await asyncio.sleep(0)

    mock_uasyncio.sleep_ms = mock_sleep_ms
    mock_uasyncio.CancelledError = asyncio.CancelledError

    with patch.dict(
        sys.modules,
        {"network": mock_network, "uasyncio": mock_uasyncio, "time": mock_time},
    ):
        if "modules.network.WiFi" in sys.modules:
            del sys.modules["modules.network.WiFi"]

        spec = importlib.util.spec_from_file_location("WiFi", "modules/network/WiFi.py")
        module = importlib.util.module_from_spec(spec)
        module.network = mock_network
        module.uasyncio = mock_uasyncio
        module.time = mock_time
        spec.loader.exec_module(module)

        yield module, mock_network, mock_uasyncio


# ---------------------------------------------------------------------------
# AP Tests
# ---------------------------------------------------------------------------


class TestApStart:
    """Tests for AP start behaviour (AC-01 through AC-04, AC-09)"""

    @pytest.mark.asyncio
    async def test_ac01_start_initiates_ap_correctly(self, wifi_module):
        """AC-01: start AP with ssid and password configures AP_IF"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        result = await wifi.ap.start(ssid="Test", password="12345678")

        ap_nic = mock_net.WLAN(mock_net.AP_IF)
        assert result is True
        assert ap_nic.active() is True
        assert ap_nic._config["essid"] == "Test"
        assert ap_nic._config["password"] == "12345678"
        assert ap_nic._config["authmode"] == 3

    @pytest.mark.asyncio
    async def test_ac02_start_open_network_no_password(self, wifi_module):
        """AC-02: start AP without password uses authmode 0"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        result = await wifi.ap.start(ssid="Open")

        ap_nic = mock_net.WLAN(mock_net.AP_IF)
        assert result is True
        assert ap_nic._config["authmode"] == 0
        assert "password" not in ap_nic._config

    @pytest.mark.asyncio
    async def test_ac02_start_open_network_empty_password(self, wifi_module):
        """AC-02: start AP with empty password uses authmode 0"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        result = await wifi.ap.start(ssid="Open", password="")

        ap_nic = mock_net.WLAN(mock_net.AP_IF)
        assert result is True
        assert ap_nic._config["authmode"] == 0

    @pytest.mark.asyncio
    async def test_ac03_start_custom_ip(self, wifi_module):
        """AC-03: start AP with custom IP stores it for getStatus"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.ap.start(ssid="Test", password="12345678", ip="10.0.0.1")

        # IP is stored but not applied via ifconfig (as per implementation note)
        status = wifi.ap.getStatus()
        assert status["ip"] == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_ac04_start_noop_when_already_active(self, wifi_module):
        """AC-04: second start is a no-op, including stored status"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.ap.start(ssid="Test", password="12345678", ip="192.168.4.1")
        ap_nic = mock_net.WLAN(mock_net.AP_IF)
        original_config = dict(ap_nic._config)
        original_status = wifi.ap.getStatus()

        result = await wifi.ap.start(ssid="Other", password="newpass", ip="10.0.0.1")

        assert result is True
        assert ap_nic._config == original_config
        assert wifi.ap.getStatus() == original_status

    @pytest.mark.asyncio
    async def test_ap_start_returns_false_when_activation_times_out(self, wifi_module):
        """AP start fails when active() never becomes True."""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi(debug=True)
        wifi._log = MagicMock()

        class StuckApWLAN(MockWLAN):
            def active(self, state=None):
                if state is None:
                    return False
                self._active = False

        stuck_ap = StuckApWLAN(mock_net.AP_IF)

        def create_wlan(interface_type):
            if interface_type == mock_net.AP_IF:
                return stuck_ap
            return MockWLAN(interface_type)

        mock_net.WLAN = create_wlan

        result = await wifi.ap.start(
            ssid="NeverUp", password="12345678", ip="10.10.10.1"
        )

        assert result is False
        assert wifi.ap.getStatus() == {"active": False, "ssid": "", "ip": ""}
        wifi._log.assert_any_call("AP activation timeout")

    @pytest.mark.asyncio
    async def test_ac09_start_returns_false_on_error(self, wifi_module):
        """AC-09: start returns False when WLAN constructor raises"""
        module, mock_net, _ = wifi_module

        def raise_error(interface):
            raise RuntimeError("Hardware failure")

        mock_net.WLAN = raise_error
        wifi = module.WiFi()

        result = await wifi.ap.start(ssid="Test", password="12345678")

        assert result is False


class TestApStop:
    """Tests for AP stop behaviour (AC-05, AC-06)"""

    @pytest.mark.asyncio
    async def test_ac05_stop_deactivates_ap(self, wifi_module):
        """AC-05: stop deactivates AP_IF and returns True"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()
        await wifi.ap.start(ssid="Test", password="12345678")

        result = wifi.ap.stop()

        ap_nic = mock_net.WLAN(mock_net.AP_IF)
        assert result is True
        assert ap_nic.active() is False

    def test_ac06_stop_noop_when_already_stopped(self, wifi_module):
        """AC-06: stop when AP was never started returns True"""
        module, _, _ = wifi_module
        wifi = module.WiFi()

        result = wifi.ap.stop()

        assert result is True


class TestApGetStatus:
    """Tests for AP getStatus (AC-07, AC-08)"""

    @pytest.mark.asyncio
    async def test_ac07_get_status_active(self, wifi_module):
        """AC-07: getStatus when AP active returns correct dict"""
        module, _, _ = wifi_module
        wifi = module.WiFi()
        await wifi.ap.start(ssid="Test", password="12345678")

        status = wifi.ap.getStatus()

        assert status == {"active": True, "ssid": "Test", "ip": "192.168.4.1"}

    def test_ac08_get_status_stopped(self, wifi_module):
        """AC-08: getStatus when AP not started returns inactive dict"""
        module, _, _ = wifi_module
        wifi = module.WiFi()

        status = wifi.ap.getStatus()

        assert status == {"active": False, "ssid": "", "ip": ""}


# ---------------------------------------------------------------------------
# STA Tests
# ---------------------------------------------------------------------------


class TestStaStart:
    """Tests for STA start behaviour (AC-10, AC-11, AC-29)"""

    @pytest.mark.asyncio
    async def test_ac10_start_activates_sta_and_launches_task(self, wifi_module):
        """AC-10: start activates STA_IF and creates async task"""
        module, mock_net, mock_async = wifi_module
        wifi = module.WiFi()

        result = await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        assert result is True
        assert sta_nic.active() is True
        mock_async.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_ac11_start_restarts_if_already_active(self, wifi_module):
        """AC-11: starting STA again cancels previous task"""
        module, _, mock_async = wifi_module
        wifi = module.WiFi()

        first_task = MockTask()
        second_task = MockTask()

        created_tasks = [first_task, second_task]

        def create_task_override(coro):
            coro.close()
            return created_tasks.pop(0)

        mock_async.create_task.side_effect = create_task_override

        await wifi.sta.start(ssid="First", password="pass1")

        await wifi.sta.start(ssid="Second", password="pass2")

        assert first_task.cancelCalled == 1

    @pytest.mark.asyncio
    async def test_sta_open_network_uses_consistent_connect_style(self, wifi_module):
        """Open-network connect calls use single-arg style in start and monitor."""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.sta.start(ssid="CafeWiFi", password=None, maxReconnects=2)
        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        assert sta_nic._connectCalls[0] == ("CafeWiFi",)

        call_count = [0]

        async def fake_sleep_ms(ms):
            call_count[0] += 1
            if call_count[0] > 2:
                raise asyncio.CancelledError()
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms
        sta_nic._connected = False

        await wifi.sta._monitor()

        assert ("CafeWiFi",) in sta_nic._connectCalls[1:]

    @pytest.mark.asyncio
    async def test_ac29_start_returns_false_on_error(self, wifi_module):
        """AC-29: start returns False when WLAN constructor raises"""
        module, mock_net, _ = wifi_module

        def raise_error(interface):
            raise RuntimeError("Hardware failure")

        mock_net.WLAN = raise_error
        wifi = module.WiFi()

        result = await wifi.sta.start(ssid="MiCasa", password="secret")

        assert result is False


class TestStaStop:
    """Tests for STA stop behaviour (AC-12, AC-13)"""

    @pytest.mark.asyncio
    async def test_ac12_stop_deactivates_and_cancels_task(self, wifi_module):
        """AC-12: stop deactivates STA_IF, cancels task, returns True"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.sta.start(ssid="MiCasa", password="secret")

        task = wifi.sta._task

        result = await wifi.sta.stop()

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        assert result is True
        assert sta_nic.active() is False
        assert task.cancelCalled == 1

    @pytest.mark.asyncio
    async def test_ac13_stop_noop_when_not_started(self, wifi_module):
        """AC-13: stop when STA was never started returns True"""
        module, _, _ = wifi_module
        wifi = module.WiFi()

        result = await wifi.sta.stop()

        assert result is True


class TestStaIsConnected:
    """Tests for STA isConnected (AC-14, AC-15)"""

    @pytest.mark.asyncio
    async def test_ac14_is_connected_true(self, wifi_module):
        """AC-14: isConnected returns True when NIC reports connected"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()
        await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._connected = True

        assert wifi.sta.isConnected() is True

    def test_ac15_is_connected_false_not_started(self, wifi_module):
        """AC-15: isConnected returns False when STA not started"""
        module, _, _ = wifi_module
        wifi = module.WiFi()

        assert wifi.sta.isConnected() is False


class TestStaGetStatus:
    """Tests for STA getStatus (AC-16, AC-17)"""

    @pytest.mark.asyncio
    async def test_ac16_get_status_connected(self, wifi_module):
        """AC-16: getStatus when connected returns correct dict"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()
        await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._connected = True
        sta_nic._ifconfig = (
            "192.168.1.105",
            "255.255.255.0",
            "192.168.1.1",
            "0.0.0.0",
        )

        status = wifi.sta.getStatus()

        assert status == {
            "connected": True,
            "ssid": "MiCasa",
            "ip": "192.168.1.105",
        }

    def test_ac17_get_status_not_connected(self, wifi_module):
        """AC-17: getStatus when not started returns disconnected dict"""
        module, _, _ = wifi_module
        wifi = module.WiFi()

        status = wifi.sta.getStatus()

        assert status == {"connected": False, "ssid": "", "ip": ""}


class TestStaScan:
    """Tests for STA scan (AC-18, AC-19)"""

    @pytest.mark.asyncio
    async def test_ac18_scan_returns_formatted_results_no_duplicates(self, wifi_module):
        """AC-18: scan deduplicates SSIDs keeping best RSSI"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()
        await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._scan_results = [
            (b"MiCasa", b"\xaa\xbb\xcc\xdd\xee\xff", 6, -45, 3, 0),
            (b"MiCasa", b"\x11\x22\x33\x44\x55\x66", 6, -70, 3, 0),
            (b"Vecino", b"\xaa\x11\x22\x33\x44\x55", 1, -60, 4, 0),
        ]

        results = await wifi.sta.scan()

        ssids = [r["ssid"] for r in results]
        assert ssids.count("MiCasa") == 1
        micasa = [r for r in results if r["ssid"] == "MiCasa"][0]
        assert micasa["rssi"] == -45
        assert micasa["channel"] == 6
        assert micasa["security"] == 3
        assert micasa["bssid"] == "aa:bb:cc:dd:ee:ff"
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_ac18_scan_filters_empty_and_hidden_ssids(self, wifi_module):
        """AC-18: scan filters out empty SSID and hidden networks"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()
        await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._scan_results = [
            (b"Visible", b"\xaa\xbb\xcc\xdd\xee\xff", 6, -45, 3, 0),
            (b"", b"\x11\x22\x33\x44\x55\x66", 6, -50, 3, 0),
            (b"Hidden", b"\xaa\x11\x22\x33\x44\x55", 1, -60, 4, 1),
        ]

        results = await wifi.sta.scan()

        ssids = [r["ssid"] for r in results]
        assert "Visible" in ssids
        assert "" not in ssids
        assert "Hidden" not in ssids
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_ac19_scan_returns_empty_without_sta_active(self, wifi_module):
        """AC-19: scan auto-activates STA and returns results (not empty anymore)"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        # Setup scan results that will be returned once STA activates
        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._scan_results = [
            (b"Network", b"\xaa\xbb\xcc\xdd\xee\xff", 6, -45, 3, 0),
        ]

        results = await wifi.sta.scan()

        # Should now auto-activate and return results
        assert sta_nic.active() is True
        assert len(results) == 1


# ---------------------------------------------------------------------------
# STA Callback / _monitor Tests
# ---------------------------------------------------------------------------


class TestStaCallbacks:
    """Tests for STA _monitor callbacks (AC-20 through AC-23)"""

    async def _build_wifi_for_monitor(self, wifi_module):
        """Helper: build a WiFi instance with real-async-compatible uasyncio."""
        module, mock_net, mock_async = wifi_module
        wifi = module.WiFi()

        # We need the STA NIC to exist before _monitor runs
        await wifi.sta.start(ssid="MiCasa", password="secret")

        sta_nic = mock_net.WLAN(mock_net.STA_IF)

        # Replace uasyncio functions with real asyncio equivalents so
        # we can drive _monitor with asyncio.run()
        module.uasyncio.CancelledError = asyncio.CancelledError

        return wifi, sta_nic, module

    @pytest.mark.asyncio
    async def test_ac20_on_connect_fires_with_ip(self, wifi_module):
        """AC-20: onConnect callback fires with IP on first connection"""
        wifi, sta_nic, module = await self._build_wifi_for_monitor(wifi_module)

        sta_nic._connected = True
        sta_nic._ifconfig = (
            "192.168.1.105",
            "255.255.255.0",
            "192.168.1.1",
            "0.0.0.0",
        )

        callback = MagicMock()
        wifi.sta.onConnect = callback

        call_count = [0]

        async def fake_sleep_ms(ms):
            call_count[0] += 1
            if call_count[0] > 1:
                raise asyncio.CancelledError()
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms

        try:
            await wifi.sta._monitor()
        except (asyncio.CancelledError, SystemExit):
            pass

        callback.assert_called_once_with("192.168.1.105")

    @pytest.mark.asyncio
    async def test_ac21_on_disconnect_fires(self, wifi_module):
        """AC-21: onDisconnect fires when connection drops"""
        wifi, sta_nic, module = await self._build_wifi_for_monitor(wifi_module)

        disconnect_cb = MagicMock()
        wifi.sta.onDisconnect = disconnect_cb

        # Sequence: connected on iteration 1, disconnected on iteration 2
        connect_sequence = iter([True, False])

        def dynamic_isconnected():
            return next(connect_sequence, False)

        sta_nic.isconnected = dynamic_isconnected
        sta_nic._ifconfig = (
            "192.168.1.105",
            "255.255.255.0",
            "192.168.1.1",
            "0.0.0.0",
        )

        call_count = [0]

        async def fake_sleep_ms(ms):
            call_count[0] += 1
            if call_count[0] > 2:
                raise asyncio.CancelledError()
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms

        try:
            await wifi.sta._monitor()
        except (asyncio.CancelledError, SystemExit):
            pass

        disconnect_cb.assert_called_once()

    @pytest.mark.asyncio
    async def test_ac22_on_reconnect_fail_after_max_attempts(self, wifi_module):
        """AC-22: onReconnectFail fires after maxReconnects exhausted"""
        wifi, sta_nic, module = await self._build_wifi_for_monitor(wifi_module)

        wifi.sta._maxReconnects = 3
        sta_nic._connected = False

        fail_cb = MagicMock()
        wifi.sta.onReconnectFail = fail_cb

        async def fake_sleep_ms(ms):
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms

        # _monitor will loop until _reconnectCount >= _maxReconnects then return
        await wifi.sta._monitor()

        fail_cb.assert_called_once()
        assert sta_nic.active() is False

    @pytest.mark.asyncio
    async def test_ac23_on_connect_fires_on_reconnection(self, wifi_module):
        """AC-23: onConnect fires again after disconnect and reconnect"""
        wifi, sta_nic, module = await self._build_wifi_for_monitor(wifi_module)

        connect_cb = MagicMock()
        wifi.sta.onConnect = connect_cb

        # Sequence: connected → disconnected → connected → cancel
        connect_sequence = iter([True, False, True])

        def dynamic_isconnected():
            return next(connect_sequence, True)

        sta_nic.isconnected = dynamic_isconnected
        sta_nic._ifconfig = (
            "192.168.1.105",
            "255.255.255.0",
            "192.168.1.1",
            "0.0.0.0",
        )

        call_count = [0]

        async def fake_sleep_ms(ms):
            call_count[0] += 1
            if call_count[0] > 3:
                raise asyncio.CancelledError()
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms

        try:
            await wifi.sta._monitor()
        except (asyncio.CancelledError, SystemExit):
            pass

        assert connect_cb.call_count == 2

    @pytest.mark.asyncio
    async def test_monitor_isolates_callback_exceptions(self, wifi_module):
        """Exceptions in callbacks are logged and do not break monitor flow."""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi(debug=True)
        wifi._log = MagicMock()

        await wifi.sta.start(ssid="MiCasa", password="secret", maxReconnects=2)
        sta_nic = mock_net.WLAN(mock_net.STA_IF)

        connect_sequence = iter([True, False, False])

        def dynamic_isconnected():
            return next(connect_sequence, False)

        sta_nic.isconnected = dynamic_isconnected
        sta_nic._ifconfig = (
            "192.168.1.110",
            "255.255.255.0",
            "192.168.1.1",
            "0.0.0.0",
        )

        wifi.sta.onConnect = lambda ip: (_ for _ in ()).throw(
            RuntimeError("connect boom")
        )
        wifi.sta.onDisconnect = lambda: (_ for _ in ()).throw(
            RuntimeError("disconnect boom")
        )
        wifi.sta.onReconnectFail = lambda: (_ for _ in ()).throw(
            RuntimeError("fail boom")
        )

        async def fake_sleep_ms(ms):
            await asyncio.sleep(0)

        module.uasyncio.sleep_ms = fake_sleep_ms

        await wifi.sta._monitor()

        assert sta_nic.active() is False
        log_messages = [call.args[0] for call in wifi._log.call_args_list]
        assert any("onConnect callback failed" in msg for msg in log_messages)
        assert any("onDisconnect callback failed" in msg for msg in log_messages)
        assert any("onReconnectFail callback failed" in msg for msg in log_messages)


# ---------------------------------------------------------------------------
# AP / STA Independence Tests
# ---------------------------------------------------------------------------


class TestApStaIndependence:
    """Tests for AP and STA independence (AC-24 through AC-27)"""

    @pytest.mark.asyncio
    async def test_ac24_ap_start_does_not_affect_sta(self, wifi_module):
        """AC-24: starting AP does not touch STA_IF"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        # Start STA first
        await wifi.sta.start(ssid="MiCasa", password="secret")
        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._connected = True

        # Start AP
        await wifi.ap.start(ssid="MyAP", password="12345678")

        assert sta_nic._connected is True
        assert sta_nic.active() is True

    @pytest.mark.asyncio
    async def test_ac25_sta_start_does_not_affect_ap(self, wifi_module):
        """AC-25: starting STA does not touch AP_IF"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.ap.start(ssid="MyAP", password="12345678")
        ap_nic = mock_net.WLAN(mock_net.AP_IF)

        await wifi.sta.start(ssid="MiCasa", password="secret")

        assert ap_nic.active() is True
        assert ap_nic._config["essid"] == "MyAP"

    @pytest.mark.asyncio
    async def test_ac26_ap_stop_does_not_affect_sta(self, wifi_module):
        """AC-26: stopping AP does not touch STA_IF"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.ap.start(ssid="MyAP", password="12345678")
        await wifi.sta.start(ssid="MiCasa", password="secret")
        sta_nic = mock_net.WLAN(mock_net.STA_IF)
        sta_nic._connected = True

        wifi.ap.stop()

        assert sta_nic.active() is True
        assert sta_nic._connected is True

    @pytest.mark.asyncio
    async def test_ac27_sta_stop_does_not_affect_ap(self, wifi_module):
        """AC-27: stopping STA does not touch AP_IF"""
        module, mock_net, _ = wifi_module
        wifi = module.WiFi()

        await wifi.ap.start(ssid="MyAP", password="12345678")
        await wifi.sta.start(ssid="MiCasa", password="secret")
        ap_nic = mock_net.WLAN(mock_net.AP_IF)

        await wifi.sta.stop()

        assert ap_nic.active() is True
        assert ap_nic._config["essid"] == "MyAP"


# ---------------------------------------------------------------------------
# Debug Mode Test
# ---------------------------------------------------------------------------


class TestDebugMode:
    """Test for debug output (AC-28)"""

    @pytest.mark.asyncio
    async def test_ac28_debug_mode_prints_messages(self, wifi_module, capsys):
        """AC-28: WiFi(debug=True) prints [WiFi Debug] messages"""
        module, _, _ = wifi_module
        wifi = module.WiFi(debug=True)

        await wifi.ap.start(ssid="Debug", password="12345678")

        captured = capsys.readouterr()
        assert "[WiFi Debug]" in captured.out
