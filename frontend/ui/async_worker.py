import asyncio
from PySide6.QtCore import QThread, Signal

class AsyncWorker(QThread):
    finished = Signal(object)
    error = Signal(Exception)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            coro = self.func(*self.args, **self.kwargs)
            result = asyncio.run(coro)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)
