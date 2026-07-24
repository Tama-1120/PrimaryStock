from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QPushButton, QLabel
)

from services.services import human_number, opendir

import pandas as pd
from datetime import datetime
from pathlib import Path

class DataFrameModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self._df = df
    
    def rowCount(self, parent = None):
        return len(self._df)
    
    def columnCount(self, parent = None):
        return len(self._df.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        
        value = self._df.iat[index.row(), index.column()]
        column = self._df.columns[index.column()]

        if column == "前日比":
            return f"{value:.2f}%"
        
        elif column == "PER":
            return f"{value:.2f}倍"
        
        elif column == "PBR":
            return f"{value:.2f}倍"

        elif column == "時価総額":
            return human_number(value)
        
        elif column == "配当利回り":
            return f"{value:.2f}%"
        
        elif column == "ROE":
            return f"{value:.2f}%"
        
        elif column == "ROA":
            return f"{value:.2f}%"
        
        elif column == "自己資本比率":
            return f"{value:.2f}"

        return str(value)
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(self._df.index[section])
            
    def sort(self, column, order):
        col_name = self._df.columns[column]

        self.layoutAboutToBeChanged.emit()

        ascending = order == Qt.SortOrder.AscendingOrder
        self._df = (
            self._df
            .sort_values(col_name, ascending=ascending)
            .reset_index(drop=True)
        )

        self.layoutChanged.emit()
            
class ResultDialog(QDialog):
    def __init__(self, parent, df):
        super().__init__(parent)

        self.setWindowTitle("PrimaryStockResult")

        windowwidth = 1440
        windowheight = 1000

        self.resize(windowwidth, windowheight)

        layout = QVBoxLayout(self)

        self.setbutton()
        layout.addWidget(self.export_button)

        df = df.sort_values(
            by="コード",
            ascending=True,
            kind="mergesort"
        )

        self.table = QTableView()
        self.table.setModel(DataFrameModel(df))
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(
            df.columns.get_loc("コード"),
            Qt.AscendingOrder
        )
        self.table.resizeColumnsToContents()

        layout.addWidget(self.table)

    def setbutton(self):
        self.export_button = QPushButton("CSV出力")
        self.export_button.clicked.connect(self.export_csv)

    def export_csv(self):
        model = self.table.model()

        rows = model.rowCount()
        cols = model.columnCount()

        headers = [
            model.headerData(c, Qt.Horizontal, Qt.DisplayRole)
            for c in range(cols)
        ]

        data = []

        for r in range(rows):
            row = []
            for c in range(cols):
                index = model.index(r, c)
                row.append(model.data(index, Qt.DisplayRole))
            data.append(row)

        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        pd.DataFrame(
            data,
            columns=headers
        ).to_csv(output_dir / f"{dt}.csv" , index=False, encoding="utf-8-sig")

        MessageDialog().exec()
        

class MessageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Message")

        layout = QVBoxLayout(self)

        self.SetLabel()
        layout.addWidget(self.closelabel)

        self.SetCloseButton()
        layout.addWidget(self.closebutton)

        self.SetDirButton()
        layout.addWidget(self.dirbutton)

    def SetLabel(self):
        self.closelabel = QLabel(self)
        self.closelabel.setText("CSV出力が完了しました")

    def SetCloseButton(self):
        self.closebutton = QPushButton("閉じる")
        self.closebutton.clicked.connect(self.close)

    def SetDirButton(self):
        self.dirbutton = QPushButton("出力ファイルを見る")
        self.dirbutton.clicked.connect(lambda:(
            opendir(),
            self.close(),
        )
    )