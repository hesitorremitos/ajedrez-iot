import asyncio


class _SSEStream:
    def __init__(self, sse):
        self._sse = sse

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self._sse._event.wait()
        self._sse._event.clear()
        return self._sse._buffer


class SSE:
    def __init__(self):
        self._event = asyncio.Event()
        self._buffer = b""

    async def send(self, data, event_id=None):
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            data = str(data).encode()

        if event_id is None:
            self._buffer = b"data: " + data + b"\n\n"
        else:
            if not isinstance(event_id, (str, bytes)):
                event_id = str(event_id)
            if isinstance(event_id, str):
                event_id = event_id.encode()
            self._buffer = b"id: " + event_id + b"\ndata: " + data + b"\n\n"

        self._event.set()

    def stream(self):
        return _SSEStream(self)
