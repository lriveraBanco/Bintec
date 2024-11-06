from pymongo import MongoClient
import gridfs

# Conectar a la base de datos "archivos"
conn = MongoClient("mongodb://localhost:27017/")
db = conn["calendario"]  
fs = gridfs.GridFS(db) 
fs_files = db["fs.files"]