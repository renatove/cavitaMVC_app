from model.model import Model
class MainController:
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.file_name = ""

    def getGeoJsonFile(self):
        try:
            self.file_name = self.model.openGeojsonFile()
            return self.file_name
        except Exception as err:
            raise Exception("Nessun file selezionato")

    def importDataFile(self):
        if len(self.file_name) == 0:
            raise ("ATTENZIONE: sfile non definito")
        try:
            data_mat = self.model.importGeojsonFile(self.file_name, "")
            return data_mat
        except Exception as err:
            raise("ATTENZIONE: si è verificato un errore")