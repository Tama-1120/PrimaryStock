import PySide6
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import QThread
import os
from services.services import search
from gui.worker import Worker
from gui.dialog import ResultDialog

#PySideのアプリ本体(コーディング部分)
class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        #ウィンドウタイトル
        self.setWindowTitle("PrimaryStock")

        #ボタン表示
        self.setButton()

    #ボタンメソッド
    def setButton(self):
        self.button = QPushButton(self)
        self.button.setText("データ取得")
        self.button.clicked.connect(self.CallbackButtonSearch)

    def CallbackButtonSearch(self):
        self.button.setEnabled(False)

        self.thread = QThread()
        self.worker = Worker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_finished(self, df):
        self.button.setEnabled(True)
        dialog = ResultDialog(self, df)
        dialog.exec()


if __name__ == "__main__":
    dirname = os.path.dirname(PySide6.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path