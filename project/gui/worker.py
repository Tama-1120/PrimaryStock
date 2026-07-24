from PySide6.QtCore import QObject, Signal
from services.services import search

class Worker(QObject):
    finished = Signal(object)
    progress = Signal(int, int)
    error = Signal(str)

    def run(self):
        try:
            df = search(progress_callback=self.progress.emit)
            self.finished.emit(df)
        except Exception as e:
            self.error.emit(str(e))