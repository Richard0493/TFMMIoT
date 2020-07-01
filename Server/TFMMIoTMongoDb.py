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
import pymongo
#################################################################################

#################################################################################
# Inicio - Definicion Funciones
def mongoDbConnect(serverAddress, database, collection):
  # Mongo Client Creation
  client = pymongo.MongoClient(serverAddress)
  # Connect to Database
  db = client[database]
  # Connect to Collection
  dbCollection = db[collection]

  return dbCollection
  
def mongoDbWrite(dbCollection, dataDb):
  
  insertResult = dbCollection.insert_one(dataDb)
  return insertResult


