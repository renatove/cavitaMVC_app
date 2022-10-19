import arcpy
import json
from PySide6 import QtWidgets
from resources.setting import model_setting
from configparser import ConfigParser

def ParseDateTime(txt):
    import datetime
    format1 = '%Y-%m-%dT%H:%M:%S'
    dt = datetime.datetime.strptime(txt, format1)
    return dt


def isBlank(myString):
    return not (myString and myString.strip())


def isNotBlank(myString):
    return bool(myString and myString.strip())


class Model():
    def __init__(self):
        cfg = ConfigParser()
        cfg.read('./CONFIG.ini')
        self.url_gis = cfg.get('PORTAL', 'INDIRIZZO_PORTAL')
        self.user = cfg.get('PORTAL', 'UTENTE')
        self.pwd = cfg.get('PORTAL', 'PASSWORD')
        self.path_images = cfg.get('DATI', 'PATH')
        self.fc = cfg.get('FEATURE CLASS', 'FC_CAVITA')
        self.fc_template = cfg.get('FEATURE CLASS', 'FC_TEMPLATE')
        self.gdb = cfg.get('GEODATABASE', 'GDB')
        self.json_file = ""

    def openGeojsonFile(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(None, "Open", "", "GeoJson (*.json)")
        if file_name[0] != '':
            self.json_file = file_name[0]
        else:
            raise Exception("ATTENZIONE: Nessun file selezionato")

    def importGeojsonFile(self):
        escapes = ''.join([chr(char) for char in range(1, 32)])
        if self.json_file != '':
            path_to_file = self.json_file
            f = open(path_to_file, 'r', encoding="utf8", errors="ignore")
            try:
                f.seek(0)
                feat_obj = json.load(f)
                nfeat = 0
                for feat in feat_obj['features']:
                    nfeat = nfeat + 1
                # print("numero punti: %d", nfeat)
                data_mat = []
                for i in range(nfeat):
                    data_item = []
                    # print("Cavita: %5d " % (i + 1))
                    # geometry
                    geom = feat_obj["features"][i]["geometry"]
                    coord = geom['coordinates']
                    long = coord[0]
                    lati = coord[1]
                    quota = coord[2]
                    # print(geom)
                    # attribute
                    prop = feat_obj["features"][i]["properties"]
                    # print(prop)
                    # attachments
                    attachments = []
                    descrizione = []
                    for a in feat_obj["features"][i]["properties"]["attachments"]:
                        # print(a)
                        attachments.append(a['filename'])
                        descrizione.append(a['descrizione'])
                    # id
                    id = feat_obj["features"][i]["id"]
                    # print(id)
                    # type
                    typ = feat_obj["features"][i]["type"]
                    # print(typ)

                    data_item.append(prop['codice_identificativo_della_cav'])
                    data_item.append(prop['codice_SSI'])
                    data_item.append(prop['regione'])
                    data_item.append(prop['provincia'])
                    data_item.append(prop['comune'])
                    data_item.append(prop['localit_frazionevia'])
                    data_item.append(prop['tipologia_primaria'])
                    data_item.append(prop['tipologia'])
                    data_item.append(prop['denominazione_comunemente_usata'])
                    if prop['note_descrittive'] is not None:
                        note_descr = prop['note_descrittive'].translate(escapes)
                    else:
                        note_descr = ''

                    k = note_descr.find("Bibliografia")
                    if k < 0:
                        note_descrittive = note_descr
                        riferimenti_bibliografici = ""
                    else:
                        note_descrittive = note_descr[0:k]
                        riferimenti_bibliografici = note_descr[k:len(note_descr)]

                    data_item.append(note_descrittive)
                    data_item.append(prop['data_di_prima_compilazione'])
                    data_item.append(prop['data_ultimo_aggiornamento'])
                    data_item.append(prop['created_user'])
                    data_item.append(prop['created_date'])
                    data_item.append(prop['last_edited_user'])
                    data_item.append(prop['last_edited_date'])
                    data_item.append(str(long))
                    data_item.append(str(lati))
                    data_item.append(str(quota))

                    if len(attachments) > 0:
                        if len(attachments[0].strip()):
                            data_item.append(self.path_images + '/' + attachments[0])
                            data_item.append(descrizione[0])
                    else:
                        data_item.append("")
                        data_item.append("")

                    if len(attachments) > 1:
                        if len(attachments[1].strip()):
                            data_item.append(self.path_images + '/' + attachments[1])
                            data_item.append(descrizione[1])
                    else:
                        data_item.append("")
                        data_item.append("")

                    data_item.append(riferimenti_bibliografici)
                    data_mat.append(data_item)
                f.close()
                return data_mat
            except Exception as err:
                raise Exception("ATTENZIONE: si è verificato un errore di import")

        else:
            raise Exception("ATTENZIONE: Nessun file selezionato")

    def saveGeoJsonFile(self):

        try:
            arcpy.env.workspace = self.gdb
            # remove old cavita e crea new cavita
            out_sr = arcpy.SpatialReference("WGS 1984")
            if arcpy.Exists(self.fc):
                arcpy.Delete_management(self.fc, "")

            geom = arcpy.Describe(self.fc_template).shapeType
            arcpy.CreateFeatureclass_management(self.gdb, self.fc, geom, self.fc_template, spatial_reference=out_sr)

            # elenco campi mappati
            source = []
            for k in model_setting.mapping_item:
                source.append(model_setting.mapping_item[k])

            # import dei dati
            campi_data = ['data_di_prima_compilazione', 'data_ultimo_aggiornamento', 'created_date', 'last_edited_date']

            model = self.tableWidget.model()
            columnCount = model.columnCount()
            rowCount = model.rowCount()
            print(rowCount)
            for row in range(model.rowCount()):
                row_data = {}
                for column in range(columnCount):
                    index = model.index(row, column)
                    text = str(model.data(index))
                    row_data[model_setting.source_item[column]] = text

                # print(row_data)
                # mapping
                row = []
                for k in model_setting.mapping_item:
                    if k in campi_data:
                        row.append(ParseDateTime(row_data[k]))
                    else:
                        row.append(row_data[k])
                print(row)

                # insert data
                with arcpy.da.InsertCursor(self.fc, ['SHAPE@'] + source) as irows:
                    _lon = float(row_data['latitudine'])
                    _lat = float(row_data['longitudine'])
                    esri_json = {
                        "x": _lon,
                        "y": _lat,
                        "spatialReference": {
                            "wkid": 4326}}
                    point = arcpy.AsShape(esri_json, True)
                    irows.insertRow([point] + [row[i] for i in range(0, len(row))])
        except:
            raise Exception("ATTENZIONE: si è verificato un errore in saveJsonFile")



