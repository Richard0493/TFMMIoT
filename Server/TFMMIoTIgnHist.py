#################################################################################
# Autor: Richard Alexander Cordova Herrera
# TRABAJO FIN DE MASTER
# CURSO 2019-2020
# MASTER EN INTERNET DE LAS COSAS
# FACULTAD DE INFORMATICA
# UNIVERSIDAD COMPLUTENSE DE MADRID
#################################################################################

#################################################################################
# Importa librerias necesarias para el funcionamiento de la aplicacion
import csv
import pymongo

from datetime import datetime
from datetime import timedelta
#################################################################################

#################################################################################
# Inicio - Definicion Funciones

#################################################################################
# Funcion dataGrap: Genera un pydictionary
def dataGraph(dateStart, dateEnd, dataAcc, dataGyr):

    dataAccAux = []
    dataGyrAux = []

    dataAccAux.append({'time' : dateStart, 
                        'sensorAccX' : dataAcc[0], 
                        'sensorAccY' : dataAcc[1], 
                        'sensorAccZ' : dataAcc[2]})

    dataAccAux.append({'time' : dateEnd, 
                        'sensorAccX' : dataAcc[0], 
                        'sensorAccY' : dataAcc[1], 
                        'sensorAccZ' : dataAcc[2]})

    dataGyrAux.append({'time' : dateStart, 
                        'sensorGyrX' : dataGyr[0], 
                        'sensorGyrY' : dataGyr[1], 
                        'sensorGyrZ' : dataGyr[2]})

    dataGyrAux.append({'time' : dateEnd, 
                        'sensorGyrX' : dataGyr[0], 
                        'sensorGyrY' : dataGyr[1], 
                        'sensorGyrZ' : dataGyr[2]})
    
    return dataAccAux, dataGyrAux
#################################################################################

#################################################################################
# Inicio Programa General
# Path General, archivos del codigo
globalPath = "/home/tfm-iot/Documentos/TFM/Ejecutables/"

# Bandera Inicio de la aplicacion
print("Incio Script: " + str(datetime.now()))
#################################################################################

#################################################################################
# Abrir archivo configuracion parametros de busqueda
archivo = open(globalPath + "TFMMIoTIgnDataSearch.txt", 'r')
dateParameters = archivo.read() 
archivo.close()

if len(dateParameters) == 0 :
    dateStart = 1577461660762
    dateEnd = 1577461668910
    cmd = 0

else:
    dateStart = int(dateParameters[0 : dateParameters.find(" ")])
    dateParametersAux = dateParameters[dateParameters.find(" ") + 1 :]
    dateEnd = int(dateParametersAux[0 : dateParametersAux.find(" ")])
    dateParametersAux = dateParametersAux[dateParametersAux.find(" ") + 1 :]
    cmd = int(dateParametersAux[0 : dateParametersAux.find(" ")])

cmdSearch = "$eq"
if cmd == 0:
    cmdSearch = "$gte"
#################################################################################

#################################################################################
# Configuracion conexion base de datos MongoDB
serverIp = "192.168.1.52"
serverIp = "cripta.fdi.ucm.es"
serverPort = "27017"
serverPort = "27118"
database = "TFMMIoT"
collection = "Dobot"

serverAddress = "mongodb://" + serverIp + ":" + serverPort + "/"

myclient = pymongo.MongoClient(serverAddress)
mydb = myclient[database]
mycol = mydb[collection]
#################################################################################

#################################################################################
# Busqueda de datos en MongoDB, correspondiente al rango 
# ingresado
queryData = mycol.find({"sensor": "movimiento", 
                        "movCode" : {cmdSearch: cmd},
                        "time" : { "$gt" : dateStart, 
                                    "$lt" : dateEnd }},{ "_id" : 0, 
                                                        "time" : 1, 
                                                        "sensorAccX" : 1,
                                                        "sensorAccZ" : 1,
                                                        "sensorAccY" : 1,
                                                        "sensorGyrX" : 1,
                                                        "sensorGyrZ" : 1,
                                                        "sensorGyrY" : 1}).sort("time", pymongo.ASCENDING)
data = list(queryData)
#################################################################################

#################################################################################
# Caso 1: No existen Datos en el rango de fechas seleccionado. 
# Accion a realizar: Busqueda del ultimo dato registrado
if (len(data) == 0 ) :
    queryData = mycol.find({"sensor": "movimiento", 
                            "time" : { "$lt" : dateEnd }},{ "_id" : 0, 
                                                            "time" : 1, 
                                                            "sensorAccX" : 1,
                                                            "sensorAccY" : 1,
                                                            "sensorAccZ" : 1,
                                                            "sensorGyrX" : 1,
                                                            "sensorGyrY" : 1,
                                                            "sensorGyrZ" : 1}).sort("time", pymongo.DESCENDING).limit(1)
    data = list(queryData)		
    
    ##############################################################
    # Caso 1.1: No existen ningun registro almacenado.
    # Accion a Realizar: Grafica con valores en 0
    if len(data) == 0 :
        dataAccAux = [0, 0, 0]
        dataGyrAux = [0, 0, 0]
        dataAcc, dataGyr = dataGraph(dateStart, dateEnd, dataAccAux, dataGyrAux)
    ##############################################################

    ##############################################################
    # Caso 1.2: Existen registros almacenados.
    # Accion a Realizar: Seleccionar ultimo valor y construir 
    # la estructura para graficar los datos
    else :
        dataAccAux = [data[0]["sensorAccX"], data[0]["sensorAccY"], data[0]["sensorAccZ"]]
        dataGyrAux = [data[0]["sensorGyrX"], data[0]["sensorGyrY"], data[0]["sensorGyrZ"]]
        dataAcc, dataGyr = dataGraph(dateStart, dateEnd, dataAccAux, dataGyrAux)
    ##############################################################

#################################################################################

#################################################################################
# Caso 2: Existen Datos en el rango de fechas seleccionado. 
# Accion a realizar: Procesar datos y construir la estructura 
# para graficar los datos
else : 
    dataSize = 6000
    if len(data) < dataSize :
        dataSize = len(data)
        
    dataToSkip = int(len(data) / dataSize)

    mycol.create_index('time')

    dataAcc = []
    dataGyr = []

    for i in range(dataSize) :
        dataAcc.append({'time'          :   data[i*dataToSkip]['time'], 
                        'sensorAccX'    :   data[i*dataToSkip]['sensorAccX'],
                        'sensorAccY'    :   data[i*dataToSkip]['sensorAccY'],
                        'sensorAccZ'    :   data[i*dataToSkip]['sensorAccZ']})

        dataGyr.append({'time'          :   data[i*dataToSkip]['time'], 
                        'sensorGyrX'   :   data[i*dataToSkip]['sensorGyrX'],
                        'sensorGyrY'   :   data[i*dataToSkip]['sensorGyrY'],
                        'sensorGyrZ'   :   data[i*dataToSkip]['sensorGyrZ']})
#################################################################################

#################################################################################
# Actualizar Ficheros dataAcc.txt y dataGyr.txt, para graficar 
# en Ignition
fileName = "TFMMIoTIgnDataAcc.txt"
file = open(globalPath + fileName, "w")
file.write(str(dataAcc))
file.close()

fileName = "TFMMIoTIgnDataGyr.txt"
file = open(globalPath + fileName, "w")
file.write(str(dataGyr))
file.close()

fileName = "TFMMIoTIgnDataSearch.txt"
file = open(globalPath + fileName, "w")
file.write(str(dateStart) + " " + str(dateEnd) + " " + str(cmd) + " Fin")
file.close()
#################################################################################

#################################################################################
# Bandera Fin del Script, imprimir datos importantes
print("Dimensiones Data Query: " + str(len(data)))
print("Dimensiones Data: " + str(len(dataAcc)))
print("Fin Script: " + str(datetime.now()))
print("Datos Consulta")
print("Fecha Inicio: " + str(dateStart) + " Fecha Fin: " + str(dateEnd))
#################################################################################
