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
from bluepy.btle import UUID, Peripheral,DefaultDelegate

import time
import struct
import paho.mqtt.client as mqtt
import TFMMIoTSensorTag
import TFMMIoTMongoDb
#################################################################################

#################################################################################
# Inicializacion Variables y Configuraciones
#broker  =   "192.168.1.52"
broker  =   "cripta.fdi.ucm.es"
#port    =   1883
port    =   6363
topic   =   "dobot/"

mondoServer     =   "192.168.1.52"
mondoServer     =   "cripta.fdi.ucm.es"
mongoPort       =   "27118"
mongoDatabase   =   "TFMMIoT"
mongoCollection =   "Dobot"
serverAddress   = "mongodb://" + mondoServer + ":" + mongoPort + "/"

tmpObjAct = 0
tmpAmbAct = 0
tmpDeadBand = 0.5

contMov = 0
contTmpObj = 0
contTmpAmb = 0
contTmp = 0

typeMov = 0
#################################################################################

#################################################################################
# Definicion de Funciones

#################################################################################
# Funcion: MQTT - Publicar mensaje
def on_publish(client,userdata,result):             
  pass
#################################################################################

#################################################################################
# Funcion: BLE - Clase
class MyDelegateSensorTag(DefaultDelegate):
    
    #############################################################################
    # Funcion: BLE - Constructor, corre una unica vez al realizar la conexion 
    def __init__(self, params):
        DefaultDelegate.__init__(self)
    #############################################################################

    #############################################################################
    # Funcion: BLE - Notificacion enviada desde SensorTag
    def handleNotification(self, cHandle, data):
        global tmpObjAct, tmpAmbAct, contTmpObj, contTmpAmb, contTmp, contMov

        #############################################################################
        # Notificacion: SensorTag - Sensor de Temperatura
        # 44 = Humedad; 36 = Temperatura
        if  cHandle == 36 :
            tmpObjValue = TFMMIoTSensorTag.tmpTransform(data[0], data[1])
            tmpAmbValue = TFMMIoTSensorTag.tmpTransform(data[2], data[3])
            contTmp += 1   

            print("SensorTag - Sensor de Humedad - Notificacion")
            print("Tmp. Sensor: " + str(tmpObjValue) + " Tmp. Ambiente: " + str(tmpAmbValue))
            
            if (tmpObjValue >= (tmpObjAct + tmpDeadBand)) | (tmpObjValue <= (tmpObjAct - tmpDeadBand)):
                tmpObjAct = tmpObjValue
                print("Tmp. Sensor: " + str(tmpObjAct))
                client.publish(topic + "tmpSensor", str(tmpObjAct))
                contTmpObj += 1
                
            if (tmpAmbValue >= (tmpAmbAct + tmpDeadBand)) | (tmpAmbValue <= (tmpAmbAct - tmpDeadBand)):
                tmpAmbAct = tmpAmbValue
                print("Tmp. Ambiente: " + str(tmpAmbAct))
                client.publish(topic + "tmpAmbiente", str(tmpAmbAct))
                contTmpAmb += 1
        #############################################################################
          
        #############################################################################
        # Notificacion: SensorTag - Sensor de Movimiento
        # 60 = Movimiento
        elif cHandle == 60 :
            print("SensorTag - Sensor de Movimiento - Notificacion")
            gyroXValue = TFMMIoTSensorTag.gyroTransform(data[0], data[1])
            gyroYValue = TFMMIoTSensorTag.gyroTransform(data[2], data[3])
            gyroZValue = TFMMIoTSensorTag.gyroTransform(data[4], data[5])

            accXValue = TFMMIoTSensorTag.accTransform(data[6], data[7])
            accYValue = TFMMIoTSensorTag.accTransform(data[8], data[9])
            accZValue = TFMMIoTSensorTag.accTransform(data[10], data[11])

            movCode = 0

            msg = str(int(time.time() * 1000000)) + " " + str(movCode) + " " \
                                + str(accXValue) + " " + str(accYValue) + " " \
                                + str(0) + " " + str(accZValue) + " " \
                                + str(gyroXValue) + " " + str(gyroYValue) + " " \
                                + str(gyroZValue)
            
            print ("Notificacion desde " + topic + " Value: "+ str(msg))
            """
            client.publish(topic + "gyrX", str(gyroXValue))
            client.publish(topic + "gyrY", str(gyroYValue))
            client.publish(topic + "gyrZ", str(gyroZValue))

            client.publish(topic + "accX", str(accXValue))
            client.publish(topic + "accY", str(accYValue))
            client.publish(topic + "accZ", str(accZValue))
            """
            #client.publish(topic + "movimiento", msg)
            
            dataMov = {
                        'time': int(time.time() * 1000),
                        'sensor' : 'movimiento',
                        'movCode' : typeMov,
                        'sensorAcc' + "X" : float(accXValue),
                        'sensorAcc' + "Y" : float(accYValue),
                        'sensorAcc' + "Z" : float(accZValue),
                        'sensorGyr' + "X" : float(gyroXValue),
                        'sensorGyr' + "Y" : float(gyroYValue),
                        'sensorGyr' + "Z" : float(gyroZValue),
                        
                    }

            contMov += 1
            TFMMIoTMongoDb.mongoDbWrite(dbCollection, dataMov)
        #############################################################################

        print("Mov: " + str(contMov) + " Tmp. Objeto: " + str(contTmpObj) + \
                                        " Tmp. Ambiente: " + str(contTmpAmb) + \
                                        " Temp. Gen: " + str(contTmp))
    
    #############################################################################      

#################################################################################

#################################################################################
# Inicio del programa principal
dbCollection = TFMMIoTMongoDb.mongoDbConnect(serverAddress, mongoDatabase, mongoCollection)
#################################################################################
# Conexion con Broker MQTT del Servidor
# Paso 1: Crear el Objeto Cliente
client= mqtt.Client("TFMMIoTSensorTag")
# Paso 2: Asginar la Funcion Callback Pub.        
client.on_publish = on_publish
# Paso 3: Establecer la conexion Broker                  
client.connect(broker,port)            
#################################################################################         

#################################################################################
# Conexion BLE con SensorTag
sensorTagMac  = "B0:91:22:EA:56:87"

# Paso 1: Creacion periferico y clase BLE
sensorTag = Peripheral(sensorTagMac, "public")
sensorTag.setDelegate( MyDelegateSensorTag(sensorTag) )

# Paso 2: Configuraciones de las caracteristicas que se van a leer

#################################################################################
# Configuracion Lectura Parametros sensor de movimiento
sensorTag.writeCharacteristic(0x003f, struct.pack('<BB', 0xBF, 0x00))
print("SensorTag - Sensor de Movimiento - Activar Sensor")

#sensorTag.writeCharacteristic(0x0041, struct.pack('<b', 0x0A))
#print("SensorTag - Sensor de Movimiento - Definicion tiempo muestreo 100ms")

sensorTag.writeCharacteristic(0x003d, struct.pack('<BB', 0x01, 0x00))
print("SensorTag - Sensor de Movimiento - Activar Notificaciones")
#################################################################################

#################################################################################
#Configuracion Lectura Parametros Sensor Humedad
#sensorTag.writeCharacteristic(0x002f, struct.pack('<B', 0x01))
#print("SensorTag - Sensor de Humedad - Activar Sensor")

#sensorTag.writeCharacteristic(0x0031, struct.pack('<B', 0x64))
#print("SensorTag - Sensor de Humedad - Definicion tiempo Notificaciones 2.5s")

#sensorTag.writeCharacteristic(0x002d, struct.pack('<BB', 0x01, 0x00))
#print("SensorTag - Sensor de Humedad - Activar Notificaciones")
#################################################################################

#################################################################################
#Configuracion Lectura Parametros sensor de Temperatura
sensorTag.writeCharacteristic(0x0027, struct.pack('<B', 0x01))
print("SensorTag - Sensor de Temperatura - Activar Sensor")

sensorTag.writeCharacteristic(0x0029, struct.pack('<B', 0xFF))
print("SensorTag - Sensor de Temperatura - Definicion tiempo muestreo 100ms")

sensorTag.writeCharacteristic(0x0025, struct.pack('<bb', 0x01, 0x00))
print("SensorTag - Sensor de Temperatura - Activar Notificaciones")
#################################################################################

#################################################################################

#################################################################################
# Lazo Principal Detectar Notificaciones
while True:
    
    try:
        if sensorTag.waitForNotifications(0.5):
            continue
        
    except():
        print("Error")
        
    print("Esperando Notificaciones")
#################################################################################

