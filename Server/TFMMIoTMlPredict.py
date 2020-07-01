# Importacion Librerias necesarias para el correcto funcionamiento
from __future__ import print_function
from datetime import datetime
from scipy import interpolate
from scipy import signal
from sklearn.externals import joblib 

# Programa Creado para comunicacion con MongoDB
import TFMMIoTMongoDb

import matplotlib.pyplot as plt
import numpy as np
import pymongo
import paho.mqtt.client as mqtt
import time

import tensorflow as tf
from tensorflow import keras
from keras.models import load_model

#################################################################################
# Inicializacion Variables y Configuraciones
broker  =   "cripta.fdi.ucm.es"
#broker  =   "192.168.1.52"
port    =   6363

mongoServer     =   "cripta.fdi.ucm.es"
#mongoServer  =   "192.168.1.52"
mongoPort       =   "27118"
mongoDatabase   =   "TFMMIoT"
mongoCollection =   "Dobot"
serverAddress   = "mongodb://" + mongoServer + ":" + mongoPort + "/"
#################################################################################


#################################################################################
# Definicion de Funciones

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
def getDataDetails(movCode, trainDateStart, trainDateEnd):
    queryData = dbCollection.find({'movCode': movCode,
                                    'time' : { "$gt" : trainDateStart, 
                                                "$lt" : trainDateEnd }}, { "_id": 0, 
                                                                    "time" : 1,
                                                                    "sensorAccX": 1,
                                                                    "sensorAccY": 1,
                                                                    "sensorAccZ": 1,
                                                                    "sensorGyrX": 1,
                                                                    "sensorGyrY": 1,
                                                                    "sensorGyrZ": 1}).sort([("time", pymongo.ASCENDING)]).limit(1500)
    data = list(queryData)
    return data
#################################################################################

################################################################################# 
# Funcion predice modelos de ML Redes Neuronales y Regresion Lineal
def predictModels(dataSensor, deep_model, modelReg, maxPoints):
    dataAccXTest = np.array(dataSensor)

    timeAccXTest = np.linspace(0, 100, dataAccXTest.shape[0])
    timeDataTest = np.linspace(0, 100, maxPoints)
    dataAccXTest = filterData(dataAccXTest)
    fun = interpolate.interp1d(timeAccXTest, dataAccXTest)
    dataInterpolTest = fun(timeDataTest)

    dataInterpolTest = np.reshape(dataInterpolTest, [1,maxPoints])
    yPred = deep_model.predict(dataInterpolTest)
    #print("Redes Neuronales:", yPred[0][0]/1000.0)
    aux = yPred[0][0]/1000.0
    yPred = modelReg.predict(dataInterpolTest)
    #print("Regresion Lineal:", yPred[0]/1000.0)

    return (aux + yPred[0]/1000.0) / 2.0
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
    print("Comando Recibido: " + msg.payload.decode('utf-8'))
    print(msg.topic)

    if (msg.topic == "dobot/movimiento/Details"):
        # num2str(movCodeTrain), " ", num2str(movCode), " ", startTimeStamp, " ", timeStamp
        data = msg.payload.decode('utf-8').split()
        movCodeTrain = int(data[0])
        movCode = int(data[1])
        dateStart = int(data[2]) / 1000
        dateEnd = int(data[3]) / 1000

        print(movCode)
        #movCode = 1
        #sensorMode = "predVel"
        dataTrainAux = getDataDetails(movCode, dateStart, dateEnd)

        dataAccXTest = []
        dataAccYTest = []
        dataAccZTest = []

        dataGiroXTest = []
        dataGiroYTest = []
        dataGiroZTest = []

        for i in range(len(dataTrainAux)):
            dataAccXTest.append(dataTrainAux[i]['sensorAccX'])
            dataAccYTest.append(dataTrainAux[i]['sensorAccY'])
            dataAccZTest.append(dataTrainAux[i]['sensorAccZ'])
            
            dataGiroXTest.append(dataTrainAux[i]['sensorGyrX'])
            dataGiroYTest.append(dataTrainAux[i]['sensorGyrY'])
            dataGiroZTest.append(dataTrainAux[i]['sensorGyrZ'])

        if (movCode == 1) :
            vel = []
            vel.append(predictModels(dataAccXTest, velModelNNAccX, velModelRegAccX, velMaxPoints))
            vel.append(predictModels(dataAccYTest, velModelNNAccY, velModelRegAccY, velMaxPoints))
            vel.append(predictModels(dataAccZTest, velModelNNAccZ, velModelRegAccZ, velMaxPoints))

            vel.append(predictModels(dataGiroXTest, velModelNNGiroX, velModelRegGiroX, velMaxPoints))
            vel.append(predictModels(dataGiroYTest, velModelNNGiroY, velModelRegGiroY, velMaxPoints))
            vel.append(predictModels(dataGiroZTest, velModelNNGiroZ, velModelRegGiroZ, velMaxPoints))

            velAvg = sum(vel) / len(vel)

            print("La Velocidad Actual es:", velAvg)
            client.publish("dobot/movimiento/velocidad", str(velAvg))

        if movCodeTrain == 2:
            if (movCode == 2) :
                fext = []
                fext.append(predictModels(dataAccXTest, fextModelNNAccX, fextModelRegAccX, fextMaxPoints))
                fext.append(predictModels(dataAccYTest, fextModelNNAccY, fextModelRegAccY, fextMaxPoints))
                fext.append(predictModels(dataAccZTest, fextModelNNAccZ, fextModelRegAccZ, fextMaxPoints))

                fext.append(predictModels(dataGiroXTest, fextModelNNGiroX, fextModelRegGiroX, fextMaxPoints))
                fext.append(predictModels(dataGiroYTest, fextModelNNGiroY, fextModelRegGiroY, fextMaxPoints))
                fext.append(predictModels(dataGiroZTest, fextModelNNGiroZ, fextModelRegGiroZ, fextMaxPoints))
                fextAvg = sum(fext) / len(fext)

                print("La Fuerza Externa Actual es:", fextAvg)
                client.publish("dobot/movimiento/fuerzaExterna", str(fext[0]))
#################################################################################

#################################################################################
# Inicio del programa principal
dbCollection = TFMMIoTMongoDb.mongoDbConnect(serverAddress, mongoDatabase, mongoCollection)
#################################################################################

globalPath = "C:\\Users\\Richard\\OneDrive\\UCM\\Master IOT\\TFM\\Programas\\Pruebas\\Modelos\\"

path = 'Velocidad\\'
f = open(globalPath + path + 'maxPoints.txt', 'r')
velMaxPoints = int(f.read())

velModelNNAccX = load_model(globalPath + path + 'velModelNNAccX.h5')
velModelNNAccY = load_model(globalPath + path + 'velModelNNAccY.h5')
velModelNNAccZ = load_model(globalPath + path + 'velModelNNAccZ.h5')

velModelNNGiroX = load_model(globalPath + path + 'velModelNNGiroX.h5')
velModelNNGiroY = load_model(globalPath + path + 'velModelNNGiroY.h5')
velModelNNGiroZ = load_model(globalPath + path + 'velModelNNGiroZ.h5')

velModelRegAccX = joblib.load(globalPath + path + 'velModelRegAccX.pkl') 
velModelRegAccY = joblib.load(globalPath + path + 'velModelRegAccY.pkl') 
velModelRegAccZ = joblib.load(globalPath + path + 'velModelRegAccZ.pkl') 

velModelRegGiroX = joblib.load(globalPath + path + 'velModelRegGiroX.pkl') 
velModelRegGiroY = joblib.load(globalPath + path + 'velModelRegGiroY.pkl') 
velModelRegGiroZ = joblib.load(globalPath + path + 'velModelRegGiroZ.pkl') 

path = 'FExterna\\'
f = open(globalPath + path + 'maxPoints.txt', 'r')
fextMaxPoints = int(f.read())

fextModelNNAccX = load_model(globalPath + path + 'fextModelNNAccX.h5')
fextModelNNAccY = load_model(globalPath + path + 'fextModelNNAccY.h5')
fextModelNNAccZ = load_model(globalPath + path + 'fextModelNNAccZ.h5')

fextModelNNGiroX = load_model(globalPath + path + 'fextModelNNGiroX.h5')
fextModelNNGiroY = load_model(globalPath + path + 'fextModelNNGiroY.h5')
fextModelNNGiroZ = load_model(globalPath + path + 'fextModelNNGiroZ.h5')

fextModelRegAccX = joblib.load(globalPath + path + 'fextModelRegAccX.pkl') 
fextModelRegAccY = joblib.load(globalPath + path + 'fextModelRegAccY.pkl') 
fextModelRegAccZ = joblib.load(globalPath + path + 'fextModelRegAccZ.pkl') 

fextModelRegGiroX = joblib.load(globalPath + path + 'fextModelRegGiroX.pkl') 
fextModelRegGiroY = joblib.load(globalPath + path + 'fextModelRegGiroY.pkl') 
fextModelRegGiroZ = joblib.load(globalPath + path + 'fextModelRegGiroZ.pkl') 


# Conexion con Broker MQTT del Servidor
# Paso 1: Crear el Objeto Cliente
client= mqtt.Client("TFMMIoTSvrMlPredict")
# Paso 2: Asginar la Funcion Callback Pub.        
client.on_publish = on_publish
client.on_connect = on_connect
client.on_message = on_message
# Paso 3: Establecer la conexion Broker                  
client.connect(broker,port)    
#print("Connect")
client.loop_forever()
client.loop_start()      
################################################################################# 
