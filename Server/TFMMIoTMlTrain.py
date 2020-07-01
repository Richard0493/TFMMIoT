from datetime import datetime
from scipy import interpolate
from scipy import signal

import TFMMIoTMongoDb

import time
import pymongo
import paho.mqtt.client as mqtt
import numpy as np
import matplotlib.pyplot as plt



import pandas as pd

import seaborn as sns
import helper as helper
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping




#################################################################################
# Inicializacion Variables y Configuraciones
broker  =   "192.168.1.52"
#broker  =   "cripta.fdi.ucm.es"
#port    =   1883
port    =   6363

mongoServer     =   "192.168.1.52"
#mongoServer     =   "cripta.fdi.ucm.es"
mongoPort       =   "27118"
mongoDatabase   =   "TFMMIoT"
mongoCollection =   "Dobot"
serverAddress   = "mongodb://" + mongoServer + ":" + mongoPort + "/"

corrAlarmSp = 0.90
#################################################################################

#################################################################################
# Definicion de Funciones

def filterData(x):

    b, a = signal.ellip(4, 0.1, 120, 0.125)  # Filter to be applied.
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

    fig, axs = plt.subplots(3)
    plt.subplots_adjust(hspace = 0.5)

    axs[0].plot(time1, data1, color = "red", linewidth = 1, linestyle = "--")
    axs[0].plot(time2, data2, color = "blue", linewidth = 1)
    axs[0].set_title('Aceleración ' + lblLegend + ' Original', fontsize = 10)
    axs[0].set_ylabel(lblLegend, fontsize = 8)
    axs[0].tick_params(labelsize = 8)
    axs[0].label_outer()
    axs[0].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    axs[1].plot(time1, data1, color = "red", linewidth = 1, linestyle = "--")
    axs[1].plot(time1, dataInterpol, color = "blue", linewidth = 1)
    axs[1].set_title('Aceleración ' + lblLegend + ' Interpolada', fontsize = 10)
    axs[1].legend((lblLegend + ' Patrón',  lblLegend + ' Actual'),   
                    prop = {'size': 8}, 
                    loc='best')
    axs[1].set_ylabel(lblLegend, fontsize = 8)
    axs[1].set_xlabel('Tiempo (seg)', fontsize = 8)
    axs[1].tick_params(labelsize = 8)
    axs[1].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    axs[2].xcorr(data1, dataInterpol)
    axs[2].set_ylim([-1, 1])
    axs[2].tick_params(labelsize = 8)
    axs[2].grid(alpha=0.5, linestyle='dashed', linewidth=0.5)

    plt.show()

    corrAux = np.corrcoef(data1, dataInterpol)

    return corrAux[0,1]
#################################################################################

#################################################################################
def getData(movCode, dateStart, dateEnd):
    print("Init")
    topic = "dobot/"
    queryData = dbCollection.find({'movCode': { '$eq': movCode },
                                    'sensorMode' : 'trainVel'}, { "_id": 0, 
                                                                        "movCode" : 1,
                                                                        "sensorMode" : 1,
                                                                        "messValue" : 1,
                                                                        "movStart": 1, 
                                                                        "movEnd": 1 }).sort([("movStart", pymongo.DESCENDING)])

    data = list(queryData)
    return data
#################################################################################

#################################################################################
def getDataTrain(data):
    dataTrain = []
    for i in range(len(data)):
        trainDateStart = int(data[i]['movStart'])
        trainDateEnd = int(data[i]['movEnd'])
        movCode = int(data[i]['movCode'])

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

        dataTrainAux = list(queryData)
        
        for j in range(len(dataTrainAux)):
            dataTrainAux[j]['messValue'] = data[i]['messValue']

        dataTrain.append(dataTrainAux)

    # topic = "dobot/"
    # queryData = dbCollection.find({'movCode': { '$eq': movCode },
    #                                 'sensorMode' : 'trainVel'}, { "_id": 0, 
    #                                                                     "movCode" : 1,
    #                                                                     "sensorMode" : 1,
    #                                                                     "messValue" : 1,
    #                                                                     "movStart": 1, 
    #                                                                     "movEnd": 1 }).sort([("movStart", pymongo.DESCENDING)])

    # data = list(queryData)
    return dataTrain
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

        if (movCodeTrain == 0) & (movCode > 0):
            getData(movCode, dateStart, dateEnd)
#################################################################################

#################################################################################
# Inicio del programa principal
dbCollection = TFMMIoTMongoDb.mongoDbConnect(serverAddress, mongoDatabase, mongoCollection)
#################################################################################
# Conexion con Broker MQTT del Servidor
# Paso 1: Crear el Objeto Cliente
#client= mqtt.Client("TFMMIoTSensorTag")
# Paso 2: Asginar la Funcion Callback Pub.        
#client.on_publish = on_publish
#client.on_connect = on_connect
#client.on_message = on_message
# Paso 3: Establecer la conexion Broker                  
#client.connect(broker,port)    
#print("Connect")
#client.loop_forever()
#client.loop_start()      
################################################################################# 
movCode = 1
dateStart = ""
dateEnd = ""
movDetails = getData(movCode, dateStart, dateEnd)
trainData = getDataTrain(movDetails)

dataAccX = []
#print(max(len(trainData[])))
dataLen = []
#Hallar el número máximo de puntos para interpolar todas las muestras
for i in range(len(trainData)):
    dataLen.append(len(trainData[i]))

maxPoints = max(dataLen)
dataAccX = np.array([])
dataAccY = np.array([])
dataAccZ = np.array([])

dataGiroX = np.array([])
dataGiroY = np.array([])
dataGiroZ = np.array([])

for i in range(len(trainData)):
    dataAux = []
    for j in range(len(trainData[i])):
        dataAux.append([trainData[i][j]['sensorAccX'], trainData[i][j]['sensorAccY'],
                        trainData[i][j]['sensorAccZ'], trainData[i][j]['sensorGyrX'], 
                        trainData[i][j]['sensorGyrY'], trainData[i][j]['sensorGyrZ']])
    
    dataAux = np.array(dataAux)
    timeAux = np.linspace(0, 100, dataAux.shape[0])
    timeData = np.linspace(0, 100, maxPoints)

    for k in range(dataAux.shape[1]):
        fun = interpolate.interp1d(timeAux, dataAux[:, k])
        dataInterpol = fun(timeData)
        dataInterpol = np.append(dataInterpol, [trainData[i][j]['messValue']])
        

        if k == 0:
            dataAccX = np.append(dataAccX, dataInterpol)
        elif k == 1:
            dataAccY = np.append(dataAccY, dataInterpol)
        elif k == 2:
            dataAccZ = np.append(dataAccZ, dataInterpol)

        elif k == 3:
            dataGiroX = np.append(dataGiroX, dataInterpol)
        elif k == 4:
            dataGiroY = np.append(dataGiroY, dataInterpol)
        elif k == 5:
            dataGiroZ = np.append(dataGiroZ, dataInterpol)


        
dataAccX = np.reshape(dataAccX, [len(trainData),maxPoints + 1])
dataAccY = np.reshape(dataAccY, [len(trainData),maxPoints + 1])
dataAccZ = np.reshape(dataAccZ, [len(trainData),maxPoints + 1])

dataGiroX = np.reshape(dataGiroX, [len(trainData),maxPoints + 1])
dataGiroY = np.reshape(dataGiroY, [len(trainData),maxPoints + 1])
dataGiroZ = np.reshape(dataGiroZ, [len(trainData),maxPoints + 1])

X = dataAccX[:, :-1]
y = dataAccX[:, -1]

print(np.shape(X))
print(np.shape(y))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)


deep_model = Sequential()
deep_model.add(Dense(32, input_shape=(X.shape[1],), activation='relu'))
deep_model.add(Dense(16, activation='relu'))
deep_model.add(Dense(8, activation='relu'))
deep_model.add(Dense(1))
deep_model.compile('adam', 'mean_squared_error')
deep_history = deep_model.fit(X_train, y_train, epochs=30, verbose=0, validation_split=0.2)

helper.plot_loss(deep_history)




#

#trainData = np.array(trainData[0])
#print(trainData)
#print(trainData.shape[0])
#print(trainData.shape[1])
#print(type(trainData[0][0]["sensorAccX"]))
#print(len(dataAccX))

