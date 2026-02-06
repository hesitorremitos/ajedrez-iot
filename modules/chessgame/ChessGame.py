"""
Modulo ChessGame para ESP32 (MicroPython).
Coordinador que compone Chess + 2 ChessClock para ofrecer una API
unica de partida con reloj.

ChessGame es parte del core (sin hardware):
- No maneja botones/GPIO.
- No renderiza display.
- No crea AccessPoint.
- No implementa transporte.

Para mantener timeout y callbacks confiables (dado que ChessClock es lazy),
los consumidores deben obtener el tiempo a traves de ChessGame y un loop
externo debe llamar periodicamente game.update() (recomendado cada 250ms).
"""

from modules.chess import Chess
from modules.chessclock import ChessClock


class ChessGame:
    """
    Coordinador de partida de ajedrez con reloj.

    Compone una instancia de Chess (motor de reglas) y dos instancias
    de ChessClock (una por color). Coordina el cambio de reloj al
    aceptar jugadas y provee undo/redo consistentes entre tablero y reloj.

    Unidad de tiempo: milisegundos (int).
    Colores: 'w' (blancas), 'b' (negras).
    """

    def __init__(self, chess=None, whiteClock=None, blackClock=None, debug=False):
        """
        Inicializa el coordinador de partida.

        Args:
            chess: instancia Chess opcional. Si None, crea una.
            whiteClock: instancia ChessClock opcional. Si None, crea una.
            blackClock: instancia ChessClock opcional. Si None, crea una.
            debug: bool para logs de diagnostico.
        """
        self._debug = debug
        self._chess = chess if chess is not None else Chess(debug=debug)
        self._whiteClock = (
            whiteClock if whiteClock is not None else ChessClock(debug=debug)
        )
        self._blackClock = (
            blackClock if blackClock is not None else ChessClock(debug=debug)
        )

        # Stacks para undo/redo
        self._moveStack = []
        self._redoMoves = []
        self._clockStateStack = []
        self._redoClockStateStack = []

        # Callbacks
        self._onMoveAccepted = None
        self._onMoveRejected = None
        self._onUndo = None
        self._onRedo = None
        self._onTimeout = None
        self._onStateChanged = None

        # Estado interno de timeout
        self._timeoutFired = False

        # Registrar handlers de timeout en cada clock
        self._whiteClock.onTimeout = self._handleWhiteTimeout
        self._blackClock.onTimeout = self._handleBlackTimeout

    def _log(self, message):
        """Log de diagnostico interno."""
        if self._debug:
            print("[ChessGame]", message)

    # ==================== Callbacks ====================

    @property
    def onMoveAccepted(self):
        return self._onMoveAccepted

    @onMoveAccepted.setter
    def onMoveAccepted(self, callback):
        self._onMoveAccepted = callback

    @property
    def onMoveRejected(self):
        return self._onMoveRejected

    @onMoveRejected.setter
    def onMoveRejected(self, callback):
        self._onMoveRejected = callback

    @property
    def onUndo(self):
        return self._onUndo

    @onUndo.setter
    def onUndo(self, callback):
        self._onUndo = callback

    @property
    def onRedo(self):
        return self._onRedo

    @onRedo.setter
    def onRedo(self, callback):
        self._onRedo = callback

    @property
    def onTimeout(self):
        return self._onTimeout

    @onTimeout.setter
    def onTimeout(self, callback):
        self._onTimeout = callback

    @property
    def onStateChanged(self):
        return self._onStateChanged

    @onStateChanged.setter
    def onStateChanged(self, callback):
        self._onStateChanged = callback

    # ==================== Interno ====================

    def _getClock(self, color):
        """Retorna el clock correspondiente al color."""
        if color == "w":
            return self._whiteClock
        return self._blackClock

    def _takeClockSnapshot(self):
        """
        Captura un snapshot del estado actual de ambos relojes.

        Returns:
            dict con whiteTime, blackTime, activeColor, running
        """
        return {
            "whiteTime": self._whiteClock.getTime(),
            "blackTime": self._blackClock.getTime(),
            "activeColor": self._chess.getTurn(),
            "running": self._getClock(self._chess.getTurn()).isRunning(),
        }

    def _restoreClockSnapshot(self, snapshot):
        """
        Restaura el estado de ambos relojes desde un snapshot.

        Pausa ambos clocks, fija tiempos, y reanuda el activo
        si el snapshot indica que estaba corriendo.
        """
        self._whiteClock.pause()
        self._blackClock.pause()
        self._whiteClock.setTime(snapshot["whiteTime"])
        self._blackClock.setTime(snapshot["blackTime"])

        if snapshot["running"]:
            self._getClock(snapshot["activeColor"]).resume()

    def _handleWhiteTimeout(self):
        """Handler interno de timeout del reloj blanco."""
        self._handleTimeout("w")

    def _handleBlackTimeout(self):
        """Handler interno de timeout del reloj negro."""
        self._handleTimeout("b")

    def _handleTimeout(self, color):
        """
        Procesa un evento de timeout para un color.

        Pausa ambos clocks y dispara onTimeout(color) una sola vez.
        """
        if self._timeoutFired:
            return

        self._timeoutFired = True
        self._whiteClock.pause()
        self._blackClock.pause()
        self._log("Timeout: %s" % color)

        if self._onTimeout:
            self._onTimeout(color)
        self._fireStateChanged()

    def _fireStateChanged(self):
        """Dispara onStateChanged si esta configurado."""
        if self._onStateChanged:
            self._onStateChanged()

    # ==================== Acceso a componentes ====================

    def getChess(self):
        """
        Retorna la instancia Chess.

        Returns:
            Chess
        """
        return self._chess

    def getWhiteClock(self):
        """
        Retorna el reloj de blancas.

        Para diagnostico/inspeccion. UI deberia usar getTime(color).

        Returns:
            ChessClock
        """
        return self._whiteClock

    def getBlackClock(self):
        """
        Retorna el reloj de negras.

        Para diagnostico/inspeccion. UI deberia usar getTime(color).

        Returns:
            ChessClock
        """
        return self._blackClock

    # ==================== Nueva partida ====================

    def start(self, baseW, baseB=None):
        """
        Inicia una nueva partida con reloj.

        1) Resetea chess.
        2) Resetea ambos clocks con baseW / baseB.
        3) Arranca el clock del turno inicial.
        4) Inicializa stacks de undo/redo.

        Args:
            baseW: int (ms) tiempo base para blancas.
            baseB: int (ms) opcional. Si None, usa baseW.

        Returns:
            True
        """
        if baseB is None:
            baseB = baseW

        # Reset de componentes
        self._chess.reset()
        self._whiteClock.reset(baseW)
        self._blackClock.reset(baseB)

        # Limpiar stacks
        self._moveStack = []
        self._redoMoves = []
        self._clockStateStack = []
        self._redoClockStateStack = []
        self._timeoutFired = False

        # Snapshot inicial
        activeColor = self._chess.getTurn()
        self._clockStateStack.append(
            {
                "whiteTime": baseW,
                "blackTime": baseB,
                "activeColor": activeColor,
                "running": True,
            }
        )

        # Arrancar el clock del turno inicial
        self._getClock(activeColor).resume()

        self._log("Start: baseW=%d, baseB=%d, active=%s" % (baseW, baseB, activeColor))
        self._fireStateChanged()
        return True

    # ==================== Tiempo ====================

    def getTime(self, color):
        """
        Retorna el tiempo restante del color indicado (ms).

        Proxy a whiteClock.getTime() / blackClock.getTime().

        Args:
            color: 'w' o 'b'

        Returns:
            int: tiempo restante en ms
        """
        return self._getClock(color).getTime()

    def getActiveColor(self):
        """
        Retorna el color del turno actual.

        Se deriva de chess.getTurn().

        Returns:
            str: 'w' o 'b'
        """
        return self._chess.getTurn()

    # ==================== Update (polling) ====================

    def update(self):
        """
        Metodo para ser llamado por el loop de UI/Display.

        Sincroniza el clock del color activo (lazy sync) llamando
        su getTime(). Si se detecta timeout, se aplica la politica
        de timeout (pausar ambos clocks y disparar onTimeout).

        Recomendado: llamar cada 250ms.

        Returns:
            True
        """
        if self._timeoutFired:
            return True

        activeColor = self._chess.getTurn()
        clock = self._getClock(activeColor)
        clock.getTime()  # Fuerza lazy sync, puede disparar timeout via handler
        return True

    # ==================== Pausa ====================

    def pause(self):
        """
        Pausa ambos clocks.

        Returns:
            True
        """
        self._whiteClock.pause()
        self._blackClock.pause()
        self._log("Pause")
        self._fireStateChanged()
        return True

    def resume(self):
        """
        Reanuda solo el clock del color activo.

        Si la partida esta en timeout, es no-op.

        Returns:
            True
        """
        if self._timeoutFired:
            self._log("Resume ignorado: timeout")
            return True

        activeColor = self._chess.getTurn()
        self._getClock(activeColor).resume()
        self._log("Resume: active=%s" % activeColor)
        self._fireStateChanged()
        return True

    # ==================== Movimiento ====================

    def confirmMove(self, moveStr):
        """
        Confirma una jugada y coordina reloj.

        Flujo:
        1) Determina moverColor = chess.getTurn().
        2) Determina wasRunning.
        3) Ejecuta chess.play(moveStr).
        4) Si ok: coordina clocks, guarda snapshot, dispara callback.
        5) Si not ok: dispara onMoveRejected.

        No bloquea movimientos por timeout; el controlador decide.

        Args:
            moveStr: str con el movimiento (ej: 'e2-e4')

        Returns:
            bool: resultado de chess.play()
        """
        moverColor = self._chess.getTurn()
        moverClock = self._getClock(moverColor)
        wasRunning = moverClock.isRunning()

        ok = self._chess.play(moveStr)

        if ok:
            # Limpiar stacks de redo
            self._redoMoves = []
            self._redoClockStateStack = []

            if wasRunning:
                # Pausar el clock del que movio (sincroniza tiempo gastado)
                moverClock.pause()

            # Guardar moveStr en stack
            self._moveStack.append(moveStr)

            # Nuevo color activo (ya cambio en chess)
            newActiveColor = self._chess.getTurn()

            if wasRunning and not self._timeoutFired:
                # Reanudar el clock del rival
                self._getClock(newActiveColor).resume()

            # Snapshot despues del switch
            self._clockStateStack.append(self._takeClockSnapshot())

            self._log("Move accepted: %s, active=%s" % (moveStr, newActiveColor))

            if self._onMoveAccepted:
                self._onMoveAccepted(moveStr)
        else:
            self._log("Move rejected: %s" % moveStr)
            if self._onMoveRejected:
                self._onMoveRejected(moveStr)

        self._fireStateChanged()
        return ok

    # ==================== Undo/Redo ====================

    def undo(self):
        """
        Deshace el ultimo movimiento aceptado y restaura estado del reloj.

        Pausa ambos clocks durante la operacion.
        Restaura el snapshot previo del reloj.

        Returns:
            bool: True si se deshizo, False si no hay movimientos
        """
        if not self._moveStack:
            self._log("Undo: no hay movimientos")
            return False

        # Pausar ambos clocks
        self._whiteClock.pause()
        self._blackClock.pause()

        ok = self._chess.undo()

        if ok:
            # Mover moveStr al redo
            moveStr = self._moveStack.pop()
            self._redoMoves.append(moveStr)

            # Mover snapshot actual al redo
            currentSnapshot = self._clockStateStack.pop()
            self._redoClockStateStack.append(currentSnapshot)

            # Restaurar snapshot previo
            if self._clockStateStack:
                prevSnapshot = self._clockStateStack[-1]
                self._restoreClockSnapshot(prevSnapshot)

            # Limpiar timeout si estabamos en timeout
            self._timeoutFired = False

            self._log("Undo: %s" % moveStr)

            if self._onUndo:
                self._onUndo(moveStr)

            self._fireStateChanged()

        return ok

    def redo(self):
        """
        Rehace el ultimo movimiento deshecho y restaura el reloj.

        Pausa ambos clocks durante la operacion.

        Returns:
            bool: True si se rehizo, False si no hay nada en redo
        """
        if not self._redoMoves:
            self._log("Redo: no hay movimientos")
            return False

        # Pausar ambos clocks
        self._whiteClock.pause()
        self._blackClock.pause()

        moveStr = self._redoMoves[-1]
        ok = self._chess.play(moveStr)

        if ok:
            self._redoMoves.pop()

            # Mover moveStr al stack principal
            self._moveStack.append(moveStr)

            # Restaurar snapshot del redo
            redoSnapshot = self._redoClockStateStack.pop()
            self._clockStateStack.append(redoSnapshot)
            self._restoreClockSnapshot(redoSnapshot)

            self._log("Redo: %s" % moveStr)

            if self._onRedo:
                self._onRedo(moveStr)

            self._fireStateChanged()

        return ok
