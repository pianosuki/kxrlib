from typing import Coroutine, Callable


class OpenerContextManager:
    def __init__(self, _open: Coroutine, close: Callable):
        self._open = _open
        self._close = close

    async def __aenter__(self):
        await self._open

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

    def __await__(self):
        return self._open.__await__()
