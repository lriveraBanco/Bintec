from pymongo import MongoClient
import gridfs

conn = MongoClient("mongodb://localhost:27017/")
db = conn["user"]
fs = gridfs.GridFS(db)

