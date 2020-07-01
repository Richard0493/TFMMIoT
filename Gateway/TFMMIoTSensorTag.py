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
#################################################################################

#################################################################################
# Inicio - Definicion Funciones
def signedInteger(value):
    if (value & 0x8000):
        value = -0x10000 + value
    return value

#Tranfor Raw Data From Sensor Tag to Gyro
def gyroTransform(value1, value2) :
    gyroValue = signedInteger((value2 << 8) | value1)
    gyroValue = (gyroValue)/(65536.00/500.00)

    return gyroValue

#Transfor Raw Data From Sensor Tag to Acc
def accTransform(value1, value2) :
    accValue = signedInteger((value2 << 8) | value1)
    accValue = (accValue)/(32768.00/2.00)

    return accValue 

#Transfor Raw Data From Sensor Tag to Temperature
def tmpTransform(value1, value2) :

	"""
    tmpValue = signedInteger((value2 << 8) | value1)
    tmpValue = (tmpValue / 65536.00) * 165.00 - 40.00
	"""
    
	SCALE_LSB = 0.03125;
	tmpValue = signedInteger((value2 << 8) | value1)
	tmpValue = ((tmpValue) >> 2)
	tmpValue = tmpValue * SCALE_LSB;

	return tmpValue

#Transfor Raw Data From Sensor Tag to Humidity
def humTransform(value1, value2) :
    humValue = ((value2 << 8) | value1) & (0xFFFC)
    humValue = (humValue / 65536.00) * 100.00

    return humValue  