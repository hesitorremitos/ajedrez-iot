import asyncio


class _SSEStream:
    def __init__(self, sse):
        self._sse = sse

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            await self._sse._event.wait()
            self._sse._event.clear()
            data = self._sse._buffer
            if data is not None:
                return data


class SSE:
    def __init__(self):
        self._event = asyncio.Event()
        self._buffer = None

    async def send(self, data):
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            data = str(data).encode()
        self._buffer = b"data: " + data + b"\n\n"
        self._event.set()

    def stream(self):
        return _SSEStream(self)
