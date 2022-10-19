from PySide6.QtWidgets import QApplication, QWidget, QGridLayout, \
    QLabel, QLineEdit, QHBoxLayout, QTableWidget, \
    QVBoxLayout, QTableWidgetItem, QPushButton, QDialog
from PySide6.QtCore import SIGNAL, QObject
from resources.setting import model_setting


class MainView(QWidget):

    def __init__(self, model, main_ctrl):
        QWidget.__init__(self)
        self.model = model
        self.mainController = main_ctrl
        self.initUI()

    def initUI(self):
        width = 900
        heigth = 700
        self.setWindowTitle("Nessun file selezionato")
        self.resize(width, heigth)
        layout = QVBoxLayout()

        tableLayout = QHBoxLayout()
        self.tableWidget = QTableWidget()

        self.tableWidget.setColumnCount(len(model_setting.source_item))
        self.tableWidget.setHorizontalHeaderLabels(model_setting.source_item)
        tableLayout.addWidget(self.tableWidget)

        QObject.connect(self.tableWidget, SIGNAL('itemSelectionChanged()'), self.print_row)

        buttonsLayout = QHBoxLayout()
        self.buttonOpen = QPushButton("Open GeoJson")
        QObject.connect(self.buttonOpen, SIGNAL('clicked()'), self.OpenGeoJsonFile)
        self.buttonImport = QPushButton("Import Data")
        self.buttonImport.setEnabled(False)
        QObject.connect(self.buttonImport, SIGNAL('clicked()'), self.ImporGeotJsonFile)
        self.buttonSave = QPushButton("Save in GDB")
        self.buttonSave.setEnabled(False)
        QObject.connect(self.buttonSave, SIGNAL('clicked()'), self.SaveGeoJsonFile)
        self.buttonPortal = QPushButton("Send to Portal")
        QObject.connect(self.buttonPortal, SIGNAL('clicked()'), self.SendToPortal)
        self.buttonPortal.setEnabled(True)
        buttonClose = QPushButton("Close")
        QObject.connect(buttonClose, SIGNAL('clicked()'), self.closeForm)

        buttonsLayout.addWidget(self.buttonOpen)
        buttonsLayout.addWidget(self.buttonImport)
        buttonsLayout.addWidget(self.buttonSave)
        buttonsLayout.addWidget(self.buttonPortal)
        buttonsLayout.addWidget(buttonClose)

        layout.addLayout(tableLayout)
        layout.addLayout(buttonsLayout)

        self.setLayout(layout)

    def OpenGeoJsonFile(self):
        try:
            self.setWindowTitle(self.mainController.getGeoJsonFile())
            self.buttonImport.setEnabled(True)
            self.buttonOpen.setEnabled(False)
        except Exception as err:
            self.setWindowTitle("Nessun file selezionato")

    def ImporGeotJsonFile(self):
        try:
            data_mat = self.mainController.importDataFile()
            for data_item in data_mat:
                count = self.tableWidget.rowCount()
                self.tableWidget.insertRow(count)
                for i in range(0, len(data_item)):
                    self.tableWidget.setItem(count, i, QTableWidgetItem(data_item[i]))
            self.buttonSave.setEnabled(True)
        except Exception as err:
            self.setWindowTitle(err)

    def SaveGeoJsonFile(self):
        try:
            self.mainController.saveGeoJsonFile()
        except Exception as err:
            self.setWindowTitle(err)

    def SendToPortal(self):
        try:
            self.mainController.sendToPortal()
        except Exception as err:
            self.setWindowTitle(err)

    def print_row(self):
        pass

    def closeForm(self):
        exit(0)
