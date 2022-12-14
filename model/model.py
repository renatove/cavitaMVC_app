import sys
import arcpy
import json
from PySide6 import QtWidgets
from resources.setting import model_setting
from configparser import ConfigParser
from datetime import datetime
import logging

# from arcgis.features.layer import FeatureLayerCollection
# from arcgis.features.layer import FeatureLayer

def ParseDateTime(txt):
    import datetime
    format1 = '%Y-%m-%dT%H:%M:%S'
    dt = datetime.datetime.strptime(txt, format1)
    return dt


def isBlank(myString):
    return not (myString and myString.strip())


def isNotBlank(myString):
    return bool(myString and myString.strip())

def init_log():
    global nome_log
    nome_log = "geositi_"+datetime.now().strftime("%d%m%Y_%H%M")+".log"
    logging.basicConfig(filename=r'.\LOG\\'+nome_log, level=logging.INFO)
    logging.info('script_startato')
    log = logging.getLogger(nome_log)
    return log

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
                raise Exception("ATTENZIONE: si ?? verificato un errore di import")

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
            raise Exception("ATTENZIONE: si ?? verificato un errore in saveJsonFile")

    def sendToPortal(self):
        from arcgis.gis import GIS
        # Lettura file di config
        sys.dont_write_bytecode = True
        gis = GIS(self.url_gis, self.user, self.pwd)
        # search_result = gis.content.search("Cavit?? artificiali v3.1C", "Feature Layer")
        search_result = gis.content.search("geodatabase_cavita_test_gdb", "Feature Layer")

        print("Connessione ...")
        if len(search_result) > 0:
            arcpy.env.workspace = self.gdb
            if arcpy.Exists(self.fc):
                cavita_item = search_result[0]
                cavita_fl = cavita_item.layers[0]
                print(cavita_fl)
                with arcpy.da.SearchCursor(self.fc, self.final_item) as cursor:

                    # coordinate della cavita
                    for row in cursor:
                        for pnt in row[0]:
                            lonp = pnt.X
                            latp = pnt.Y

                        record_dict = {
                            "attributes":
                                {
                                    "codice_identificatico_catasto_s": row[1],
                                    "denominazione_comunemente_usata": row[2],
                                    "data_di_prima_compilazione": row[3],
                                    "data_ultimo_aggiornamento": row[4],
                                    "regione": row[5],
                                    "provincia": row[6],
                                    "comune": row[7],
                                    "localit_frazionevia": row[8],
                                    "latitudine_dd": row[9],
                                    "longitudine_dd": row[10],
                                    "tipologia_primaria": row[11],
                                    "tipologia": row[12],
                                    "note_generali": row[13],
                                    "riferimenti_bibliografici": row[14],
                                    "created_date": row[15],
                                    "created_user": row[16],
                                    "last_edited_date": row[17],
                                    "last_edited_user": row[18],
                                    "quota_altimetrica": row[19]
                                },
                            "geometry": {"x": lonp, "y": latp, "spatialReference": {"wkid": 4326}}
                        }
                        new_record = cavita_fl.edit_features(adds=[record_dict])
                        rec = new_record['addResults']
                        rec_dict = rec[0]
                        idobj = rec_dict['objectId']
                        print("insert record id: " + str(idobj))

                        # add attach
                        if isNotBlank(row[20]):
                            print("insert attach --> " + row[20])
                            cavita_fl.attachments.add(idobj, row[20])
                        if isNotBlank(row[22]):
                            print("insert attach --> " + row[22])
                            cavita_fl.attachments.add(idobj, row[22])

                    # stampa il numero di elementi inseriti
                    print(cavita_fl.query(return_count_only=True))

            else:
                print("Errore: la feature class  " + self.fc + " non esiste!")
                return

