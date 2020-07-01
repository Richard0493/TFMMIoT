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
from __future__ import print_function

import time
    
import paho.mqtt.client as mqtt
import TFMMIoTMongoDb
#################################################################################

#################################################################################
# Inicializacion Variables y Configuraciones
#broker          =   "192.168.1.52"
broker          =   "cripta.fdi.ucm.es"
port            =   6363

#mongoServer     =   "192.168.1.52"
mongoServer     =   "cripta.fdi.ucm.es"
mongoPort       =   "27118"
mongoDatabase   =   "TFMMIoT"
mongoCollection =   "Dobot"
serverAddress   = "mongodb://" + mongoServer + ":" + mongoPort + "/"
topic = "dobot/"

contTmpAmb = 0
contTmpObj = 0
contMov    = 0
contMovDetails = 0
#################################################################################


#################################################################################
# Inicio - Definicion Funciones

#################################################################################
# Funcion: Publicar mensajes MQTT
def on_publish(client,userdata,result):             
  pass
#################################################################################

#################################################################################
# Funcion: Conexion con Borker MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    client.subscribe("dobot/tmpSensor")
    client.subscribe("dobot/tmpAmbiente")
    client.subscribe("dobot/movimiento")
    client.subscribe("dobot/movimiento/#")
#################################################################################

#################################################################################
# Funcion: Detectar mensajes MQTT
def on_message(client, userdata, msg):
    global contTmpAmb, contTmpObj, contMov, contMovDetails
        
    # Temperatura Sensor
    if msg.topic == topic + "tmpSensor" :
        print("Recibido desde Temp. Sensor")
        print(int(time.time() * 1000))
        dataTmp = {
                'time' : int(time.time() * 1000),
                'sensor' : 'temperatura',
                'tmpSensor' : float(msg.payload.decode('utf-8'))
            }
        contTmpObj += 1
        TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataTmp)

    # Temperatura Ambiente
    elif msg.topic == topic + "tmpAmbiente" :
        print("Recibido desde Temp. Ambiente")
        print(int(time.time() * 1000))
        dataTmp = {
                'time' : int(time.time() * 1000),
                'sensor' : 'temperatura',
                'tmpAmbient' : float(msg.payload.decode('utf-8'))
            }
        contTmpAmb += 1
        TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataTmp)

    # Movimientos
    elif msg.topic == topic + "movimiento" :
        data = msg.payload.decode('utf-8').split()

        dataMov = {
                    'time': int(int(data[0]) / 1000),
                    'sensor' : 'movimiento',
                    'movCode' : int(data[1]),
                    'sensorAcc' + "X" : float(data[2]),
                    'sensorAcc' + "Y" : float(data[3]),
                    'sensorAcc' + "Z" : float(data[5]),
                    'sensorGyr' + "X" : float(data[6]),
                    'sensorGyr' + "Y" : float(data[7]),
                    'sensorGyr' + "Z" : float(data[8])
                }

        contMov += 1

        TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataMov)
        
    # Detalle Movimiento
    elif msg.topic == topic + "movimiento/Details" :
        data = msg.payload.decode('utf-8').split()
        sensorMode = 'normal'

        if int(data[0]) == 1:
            sensorMode = 'train'

        elif int(data[0]) == 2:
            sensorMode = 'predVel'

        elif int(data[0]) == 3:
            sensorMode = 'trainVel'

        if sensorMode == 'trainVel':

            dataMov = { 'movCode' : int(data[1]),
                        'sensorMode' : sensorMode,
                        'messValue' : float(data[4]),
                        'movStart'    : int(int(data[2]) / 1000),
                        'movEnd'       : int(int(data[3]) / 1000)
                    }
        else:
            dataMov = { 'movCode' : int(data[1]),
                        'sensorMode' : sensorMode,
                        'movStart'    : int(int(data[2]) / 1000),
                        'movEnd'       : int(int(data[3]) / 1000)
                    }
        
        TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataMov)
        contMovDetails += 1
    
#################################################################################
# Inicio del programa principal
print("Inicio Programa Server", end = '\n\n')
dbCollection = TFMMIoTMongoDb.mongoDbConnect(serverAddress, mongoDatabase, mongoCollection)
print("----------Conectado a MongoDB----------")
print("Server: " + serverAddress, "Database: " + mongoDatabase, "Collection: " + mongoDatabase, sep = '\n', end = '\n\n') 
#################################################################################

#################################################################################
# Conexion con Broker MQTT del Servidor
# Paso 1: Crear el Objeto Cliente
client= mqtt.Client("TFMMIoTSvrMqttSubscribe")
# Paso 2: Asginar la Funcion Callback Pub. 
client.on_publish = on_publish
# Paso 3: Establecer Funcion Conexion Broker.
client.on_connect = on_connect
# Paso 4: Establecer Funcion Recibir Mensajes.
client.on_message = on_message
# Paso 5: Establecer la conexion Broker.
client.connect(broker,port) 
print("----------Conectado a Broker MQTT----------")
print("Server: " + broker, "Puerto: " + str(port), sep = '\n', end = '\n\n')
# Paso 6: Bucle Quedar a la escucha nuevos mensajes.
client.loop_forever()
client.loop_start()
#################################################################################