from pymongo import MongoClient

def connect_database():
  client = MongoClient('localhost', 27017)
  db = client['tutor_agent']
  user_collection = db['user']
  room_collection = db['room']
  return user_collection, room_collection