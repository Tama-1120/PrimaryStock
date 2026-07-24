import PySide6
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt
import os
from services.services import search
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
        button = QPushButton(self)
        button.setText("データ取得")
        button.clicked.connect(self.CallbackButtonSearch)

    def CallbackButtonSearch(self):
        print("データ取得中")
        df = search()
        dialog = ResultDialog(df)
        print("データ取得完了")
        dialog.exec()


if __name__ == "__main__":
    dirname = os.path.dirname(PySide6.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path