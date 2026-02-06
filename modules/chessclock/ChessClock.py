"""
Modulo ChessClock para ESP32 (MicroPython).
Contador regresivo lazy para ajedrez. Una instancia por jugador.

El descuento de tiempo es lazy: se calcula al consultar o modificar estado,
no mediante timers ni threads. Esto implica que el callback onTimeout solo
se dispara cuando se invoca getTime(), pause(), setTime() o addTime().
Un coordinador externo debe hacer polling periodico si necesita detectar
timeout sin interaccion del usuario.
"""

import time


class ChessClock:
    """
    Contador regresivo individual para ajedrez.

    Cada instancia representa un solo reloj. Un coordinador externo
    (ej: ChessGame) crea 2 instancias y decide cual corre.

    Unidad estandar: milisegundos (int).

    El descuento es lazy: se aplica en getTime(), pause(), setTime(),
    addTime() y cualquier punto que requiera estado consistente.
    El callback onTimeout() solo se dispara durante estas sincronizaciones.
    """

    _DEFAULT_INITIAL = 300000  # 5 minutos en ms

    def __init__(self, debug=False):
        """
        Inicializa un nuevo reloj de ajedrez.

        Args:
            debug: Habilita modo debug para mensajes de diagnostico
        """
        self._debug = debug
        self._initial = None
        self._time = 0
        self._running = False
        self._lastTick = 0
        self._timeoutNotified = False

        # Callback
        self._onTimeout = None

    def _log(self, message):
        """Log de diagnostico interno."""
        if self._debug:
            print("[ChessClock]", message)

    # ==================== Callback ====================

    @property
    def onTimeout(self):
        return self._onTimeout

    @onTimeout.setter
    def onTimeout(self, callback):
        self._onTimeout = callback

    # ==================== Interno ====================

    def _sync(self):
        """
        Sincroniza el tiempo restante con el reloj monotonic.

        Descuenta el tiempo transcurrido desde el ultimo tick.
        Si el tiempo llega a 0, ejecuta auto-pause y dispara
        onTimeout una sola vez.
        """
        if not self._running:
            return

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._lastTick)
        self._lastTick = now

        self._time = self._time - elapsed
        if self._time <= 0:
            self._time = 0
            self._running = False
            self._log("Timeout: tiempo agotado")
            self._notifyTimeout()

    def _notifyTimeout(self):
        """Dispara onTimeout una sola vez por evento de timeout."""
        if not self._timeoutNotified:
            self._timeoutNotified = True
            if self._onTimeout:
                self._onTimeout()

    def _resolveInitial(self, initial):
        """
        Resuelve el valor de initial.

        Si initial es provisto, lo guarda y retorna.
        Si no, usa el guardado o el default (5 min).
        """
        if initial is not None:
            self._initial = initial
        elif self._initial is None:
            self._initial = self._DEFAULT_INITIAL
        return self._initial

    # ==================== Control ====================

    def start(self, initial=None):
        """
        Inicia el reloj (lo deja corriendo).

        Si initial es provisto, guarda initial, setea time=initial,
        limpia timeoutNotified y arranca.
        Si initial no es provisto, usa el guardado o default 5 min.

        Para reanudar despues de pausar, usar resume().

        Args:
            initial: int (ms) opcional. Tiempo base del reloj.

        Returns:
            True
        """
        resolved = self._resolveInitial(initial)
        self._time = resolved
        self._timeoutNotified = False
        self._running = True
        self._lastTick = time.ticks_ms()
        self._log("Start: initial=%d ms" % resolved)
        return True

    def pause(self):
        """
        Pausa el reloj.

        Si estaba corriendo, sincroniza el descuento hasta ahora
        antes de detener. Si ya estaba pausado, es no-op.

        Returns:
            True
        """
        if self._running:
            self._sync()
            self._running = False
            self._log("Pause: time=%d ms" % self._time)
        return True

    def resume(self):
        """
        Reanuda el reloj desde el time actual.

        Si time es 0, no vuelve a correr (no-op).
        Si ya estaba corriendo, es no-op.

        Returns:
            True
        """
        if self._running:
            return True
        if self._time <= 0:
            self._log("Resume ignorado: time=0")
            return True

        self._running = True
        self._lastTick = time.ticks_ms()
        self._log("Resume: time=%d ms" % self._time)
        return True

    # ==================== Configuracion / Reset ====================

    def reset(self, initial=None):
        """
        Deja el reloj en estado pausado con time=initial.

        Si initial es provisto, lo guarda. Si no hay initial guardado
        y no se pasa parametro, usa default 5 min.

        Limpia timeoutNotified para permitir nuevo timeout.

        Args:
            initial: int (ms) opcional.

        Returns:
            True
        """
        resolved = self._resolveInitial(initial)
        self._time = resolved
        self._running = False
        self._timeoutNotified = False
        self._log("Reset: initial=%d ms" % resolved)
        return True

    # ==================== Ajustes de Tiempo ====================

    def setTime(self, ms):
        """
        Fija el tiempo restante actual.

        Si el reloj esta corriendo, sincroniza primero, aplica el
        cambio y continua corriendo desde ese instante.
        Si el resultado es 0, entra en timeout: auto-pause y
        dispara onTimeout una sola vez.

        Args:
            ms: int (ms). Se clamplea a >= 0.

        Returns:
            True
        """
        if self._running:
            self._sync()

        self._time = ms if ms > 0 else 0

        if self._time == 0:
            self._running = False
            self._notifyTimeout()
        elif self._running:
            self._lastTick = time.ticks_ms()

        self._log("setTime: time=%d ms" % self._time)
        return True

    def addTime(self, delta):
        """
        Ajuste relativo del tiempo.

        Si el reloj esta corriendo, sincroniza primero, aplica,
        y sigue corriendo. Clamp final a >= 0.
        Si el resultado es 0, aplica politica de timeout.

        Args:
            delta: int (ms). Puede ser negativo.

        Returns:
            True
        """
        if self._running:
            self._sync()

        self._time = self._time + delta
        if self._time < 0:
            self._time = 0

        if self._time == 0:
            self._running = False
            self._notifyTimeout()
        elif self._running:
            self._lastTick = time.ticks_ms()

        self._log("addTime: delta=%d, time=%d ms" % (delta, self._time))
        return True

    # ==================== Consultas ====================

    def getTime(self):
        """
        Retorna el tiempo restante en ms.

        Si running=True, sincroniza lazy antes de devolver.
        El callback onTimeout puede dispararse durante esta llamada.

        Returns:
            int: tiempo restante en ms (>= 0)
        """
        self._sync()
        return self._time

    def getSeconds(self):
        """
        Retorna tiempo restante en segundos (floor).

        Returns:
            int: time // 1000
        """
        return self.getTime() // 1000

    def getText(self):
        """
        Retorna string MM:SS usando floor.

        Minutos pueden exceder 59 (ej: 90 min => '90:00').

        Returns:
            str: formato 'MM:SS'
        """
        totalSeconds = self.getTime() // 1000
        minutes = totalSeconds // 60
        seconds = totalSeconds % 60
        return "%d:%02d" % (minutes, seconds)

    def isRunning(self):
        """
        Indica si el reloj esta corriendo.

        Returns:
            bool
        """
        return self._running

    def isTimeout(self):
        """
        Indica si el reloj ha llegado a 0.

        Sincroniza lazy antes de evaluar.

        Returns:
            bool: True si getTime() retorna 0
        """
        return self.getTime() == 0
