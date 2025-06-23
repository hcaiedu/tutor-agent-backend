#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@filename: database.py
@description: basic function of mongodb connection   
@time: 2025/06/22
@author: Haoli WANG
@Version: 1.0
'''

from pymongo import MongoClient

def connect_database():
  """
  Description: 
    database connection
  Parameters:
    None
  Returns:
    user_collection(mongodb collection): the user/student collection which stores students' basic info and profiles
    room_collection(mongodb collection): the room collection which stores room's basic info and conversation history
  Outputs:
    None
  """
  client = MongoClient('localhost', 27017)
  db = client['tutor_agent']
  user_collection = db['user']
  room_collection = db['room']
  return user_collection, room_collection