class _Logger:
    def __init__(self, name=""):
        self.name = name

    def _emit(self, level, *args):
        try:
            if args:
                print("[%s]" % level, *args)
        except Exception:
            pass

    def debug(self, *args):
        self._emit("DEBUG", *args)

    def info(self, *args):
        self._emit("INFO", *args)

    def warning(self, *args):
        self._emit("WARN", *args)

    def error(self, *args):
        self._emit("ERROR", *args)

    def exception(self, *args):
        self._emit("EXC", *args)


def getLogger(name=""):
    return _Logger(name)
