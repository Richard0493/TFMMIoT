#################################################################################
# Autor: Richard Alexander Cordova Herrera
# TRABAJO FIN DE MASTER
# CURSO 2019-2020
# MASTER EN INTERNET DE LAS COSAS
# FACULTAD DE INFORMATICA
# UNIVERSIDAD COMPLUTENSE DE MADRID
#################################################################################

#################################################################################
# Importacion Librerias necesarias para el correcto funcionamiento
from __future__ import print_function
from datetime import datetime
from scipy import interpolate
from scipy import signal

# Programa Creado para comunicacion con MongoDB
import TFMMIoTMongoDb

# import matplotlib.pyplot as plt
import numpy as np
import pymongo
import paho.mqtt.client as mqtt
import time
#################################################################################

#################################################################################
# Inicializacion Variables y Configuraciones
broker  =   "cripta.fdi.ucm.es"
port    =   6363

mongoServer     =   "cripta.fdi.ucm.es"
mongoPort       =   "27118"
mongoDatabase   =   "TFMMIoT"
mongoCollection =   "Dobot"
serverAddress   = "mongodb://" + mongoServer + ":" + mongoPort + "/"

# Configuracion Alarma Correlacion
corrAlarmSp = 0.85
#################################################################################

#################################################################################
# Inicio - Definicion Funciones

#################################################################################
# Funcion para realizar filtro de la senal de entrada, elimina ruido.
# Devuelve la senal filtrada.
def filterData(x):

    b, a = signal.ellip(4, 0.1, 120, 0.125)
    sig = x

    fgust = signal.filtfilt(b, a, sig, method="gust")
    fpad = signal.filtfilt(b, a, sig, padlen=50)

    # plt.plot(sig, 'k-', color = "red", linewidth = 1, linestyle = "--", label='input')
    # plt.plot(fgust, 'b-', linewidth=1, label='gust')
    # plt.plot(fpad, 'c-', linewidth=1.5, label='pad')
    # plt.legend(loc='best')
    # plt.show()

    return fgust
#################################################################################

#################################################################################
# Funcion para calcular y graficar la correlacion de las senales.
# En produccion se comentara la parte de las graficas.
def corrGraph(data1, time1, data2, time2, lblLegend):
    fun = interpolate.interp1d(time2, data2)
    dataInterpol = fun(time1)

    dataInterpol = filterData(dataInterpol)
    data2 = filterData(data2)
    data1 = filterData(data1)

    # plt.plot(time1, data1, color = "red", linewidth = 1, linestyle = "--", label='Patron')
    # plt.plot(time1, dataInterpol, color = "blue", linewidth = 1, label='Actual')
    # plt.legend(loc='best')
    # plt.show()

    # fig, axs = plt.subplots(3)
    # plt.subplots_adjust(hspace = 0.5)

    # axs[0].plot(time1, data1, color = "red", linewidth = 1, linestyle = "--")
    # axs[0].plot(time2, data2, color = "blue", linewidth = 1)
    # axs[0].set_title('Aceleracion ' + lblLegend + ' Original', fontsize = 10)
    # axs[0].set_ylabel(lblLegend, fontsize = 8)
    # axs[0].tick_params(labelsize = 8)
    # axs[0].label_outer()
    # axs[0].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    # axs[1].plot(time1, data1, color = "red", linewidth = 1, linestyle = "--")
    # axs[1].plot(time1, dataInterpol, color = "blue", linewidth = 1)
    # axs[1].set_title('Aceleracion ' + lblLegend + ' Interpolada', fontsize = 10)
    # axs[1].legend((lblLegend + ' Patron',  lblLegend + ' Actual'),   
    #                 prop = {'size': 8}, 
    #                 loc='best')
    # axs[1].set_ylabel(lblLegend, fontsize = 8)
    # axs[1].set_xlabel('Tiempo (seg)', fontsize = 8)
    # axs[1].tick_params(labelsize = 8)
    # axs[1].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    # axs[2].xcorr(data1, dataInterpol)
    # axs[2].set_ylim([-1, 1])
    # axs[2].tick_params(labelsize = 8)
    # axs[2].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    # plt.show()

    corrAux = np.corrcoef(data1, dataInterpol)

    return corrAux[0,1]
#################################################################################

#################################################################################
# Funcion realiza la consulta del movimiento en la base de datos.
def getData(movCode, dateStart, dateEnd):
    topic = "dobot/"
    queryData = dbCollection.find({'movCode': { '$eq': movCode },
                                    'sensorMode' : 'train',
                                    "movStart" : { '$exists': 'true' },
                                    "movEnd" : { '$exists': 'true' }}, { "_id": 0, 
                                                                        "movCode" : 1,
                                                                        "movStart": 1, 
                                                                        "movEnd": 1 }).sort([("movStart", pymongo.DESCENDING)]).limit(1)

    data = list(queryData)

    if (len(data) > 0 ):
        trainDateStart = int(data[0]['movStart'])
        trainDateEnd = int(data[0]['movEnd'])
        movCode = int(data[0]['movCode'])

    #print(datetime.fromtimestamp(trainDateStart/1000.0))
    #print(datetime.fromtimestamp(trainDateEnd/1000.0))
    #print("Inicio: " + str(trainDateStart) + " Fin: " + str(trainDateEnd))

    queryData = dbCollection.find({'movCode': movCode,
                                    'time' : { "$gt" : trainDateStart, 
                                                "$lt" : trainDateEnd }}, { "_id": 0, 
                                                                    "time" : 1,
                                                                    "sensorAccX": 1,
                                                                    "sensorAccY": 1,
                                                                    "sensorAccZ": 1,
                                                                    "sensorGyrX": 1,
                                                                    "sensorGyrY": 1,
                                                                    "sensorGyrZ": 1}).sort([("time", pymongo.ASCENDING)]).limit(1000)

    data = list(queryData)

    dataTrain = []

    for i in range(len(data)):
        dataTrain.append([data[i]['sensorAccX'], data[i]['sensorAccY'], 
                        data[i]['sensorAccZ'], data[i]['sensorGyrX'], 
                        data[i]['sensorGyrY'], data[i]['sensorGyrZ']])
                        
    dataTrain = np.array(dataTrain)
    timeTrain = np.linspace(0, 100, len(data))

    #print(datetime.fromtimestamp(dateStart/1000))
    #print(datetime.fromtimestamp(dateEnd/1000))
    #print("Inicio: " + str(dateStart) + " Fin: " + str(dateEnd))

    queryData = dbCollection.find({'movCode': movCode,
                                    'time' : { "$gt" : dateStart, 
                                                "$lt" : dateEnd }}, { "_id": 0, 
                                                                    "time" : 1,
                                                                    "sensorAccX": 1,
                                                                    "sensorAccY": 1,
                                                                    "sensorAccZ": 1,
                                                                    "sensorGyrX": 1,
                                                                    "sensorGyrY": 1,
                                                                    "sensorGyrZ": 1}).sort([("time", pymongo.ASCENDING)]).limit(1000)

    data = list(queryData)

    dataEval = []

    for i in range(len(data)):
        dataEval.append([data[i]['sensorAccX'], data[i]['sensorAccY'],
                        data[i]['sensorAccZ'], data[i]['sensorGyrX'], 
                        data[i]['sensorGyrY'], data[i]['sensorGyrZ']])

    dataEval = np.array(dataEval)
    timeData = np.linspace(0, 100, len(data))

    corrMatrix = []
    accMatrix = ["AccX", "AccY", "AccZ", "GiroX", "GiroY", "GiroZ"]

    for i in range(dataEval.shape[1]):
        corrMatrix.append(corrGraph(dataTrain[:, i], timeTrain, dataEval[:, i], timeData, accMatrix[i]))

    for i in range(len(corrMatrix)):
        #Publicar Alarmas
        client.publish(topic + "movimiento/signal" + str(i + 1), str(corrMatrix[i]))

        if corrMatrix[i] < corrAlarmSp :
            timeStampAlm = int(time.time() * 1000)
            dataAlm = {'almSensorCode' : accMatrix[i],
                        'almValue' : corrMatrix[i],
                        'almTime' : timeStampAlm,
                        'almMovCode' : movCode,
                        'almMovStart' : dateStart,
                        'almMovEnd' : dateEnd
                    }
            #print(dataAlm)
            TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataAlm)
#################################################################################

#################################################################################
# Funcion: MQTT - Publicar mensaje
def on_publish(client,userdata,result):             
    pass
#################################################################################

#################################################################################
# Funcion: MQTT - Suscribir a un topico
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("dobot/movimiento/Details")            
#################################################################################

#################################################################################
# Funcion: MQTT - Recibe un mensaje
def on_message(client, userdata, msg):
    if (msg.topic == "dobot/movimiento/Details"):
        data = msg.payload.decode('utf-8').split()
        movCodeTrain = int(data[0])
        movCode = int(data[1])
        dateStart = int(data[2]) / 1000
        dateEnd = int(data[3]) / 1000

        # En el caso de que sea un movimiento normal, se debe aplicar el 
        # algortimo de deteccion de anomalias.
        if (movCodeTrain == 0) & (movCode > 0):
            getData(movCode, dateStart, dateEnd)
#################################################################################

#################################################################################
# Inicio del programa principal
print("Inicio Programa Server", "TFMMIoTSignalCorr", sep = '\n', end = '\n\n')
dbCollection = TFMMIoTMongoDb.mongoDbConnect(serverAddress, mongoDatabase, mongoCollection)
print("----------Conectado a MongoDB----------")
print("Server: " + serverAddress, "Database: " + mongoDatabase, "Collection: " + mongoDatabase, sep = '\n', end = '\n\n') 
#################################################################################
# Conexion con Broker MQTT del Servidor
# Paso 1: Crear el Objeto Cliente
client= mqtt.Client("TFMMIoTSignalCorr")
# Paso 2: Asginar la Funcion Callback Pub.        
client.on_publish = on_publish
client.on_connect = on_connect
client.on_message = on_message
# Paso 3: Establecer la conexion Broker                  
client.connect(broker,port)   
print("----------Conectado a Broker MQTT----------")
print("Server: " + broker, "Puerto: " + str(port), sep = '\n', end = '\n\n') 
client.loop_forever()
client.loop_start()      
################################################################################# 
