from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from threading import Lock
from threading import Thread
from flask_cors import CORS
from datetime import datetime
from openai import OpenAI
import eventlet
from llm import query_api
import os
import json
import random
import random
import string
import time

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
lock = Lock()

room_counters = {}

def generate_random_string(length):
    # 定义字符集合，包括大小写字母和数字
    characters = string.ascii_letters + string.digits
    # 从字符集合中随机选择指定数量的字符
    return ''.join(random.choices(characters, k=length))

def save_message_to_json(data):
  JSON_FILE = 'data/room/' + data["roomId"] + '.json'
  with open(JSON_FILE, "r") as file:
    old_data = json.load(file)
    if "history" not in old_data or not isinstance(old_data["history"], list):
      old_data["history"] = []
    old_data["history"].append(data)
    with open(JSON_FILE, 'w') as f:
      json.dump(old_data, f, ensure_ascii=False, indent=2) 


@app.route("/")
def home():
    return "Welcome to the Flask Backend!"

# get user info
@app.route("/user/get_user_info", methods=["OPTIONS","GET"])
def get_user_info():
  JSON_FILE = 'data/user/' + request.args.get('userName') + '.json'
  if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as file:
        data = json.load(file)
    return jsonify(data), 200
  else:
    return jsonify({"error": "User not found"}), 404
  
# update user cogitive
@app.route("/user/update_cognitive", methods=["OPTIONS","get"])
def update_cognitive():
    try:
      JSON_FILE = 'data/user/' + request.args.get('userName') + '.json'
      with open(JSON_FILE, "r") as file:
        old_data = json.load(file)
        old_data["cognitiveLevel"]["Joy"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Trust"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Fear"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Surprise"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Anger"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Disgust"].append(round(random.random(),2))
        old_data["cognitiveLevel"]["Engagement"].append(round(random.random(),2))
        old_data["tracingX"].append(datetime.now().strftime("%I:%M:%S %p"))
        # 4. 将更新后的数据写回文件
        with open(JSON_FILE, 'w') as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        res = {
          "cognitive_level":[
            old_data["cognitiveLevel"]["Joy"][-1],
            old_data["cognitiveLevel"]["Trust"][-1],
            old_data["cognitiveLevel"]["Fear"][-1],
            old_data["cognitiveLevel"]["Surprise"][-1],
            old_data["cognitiveLevel"]["Anger"][-1],
            old_data["cognitiveLevel"]["Disgust"][-1]
          ],
          "tracingX":old_data["tracingX"][-5:],
          "tracingY":[
            {
              "name":"Engagement",
              "data":old_data["cognitiveLevel"]["Engagement"][-5:]
            },
            {
              "name":"Joy",
              "data":old_data["cognitiveLevel"]["Joy"][-5:]
            },
            {
              "name":"Trust",
              "data":old_data["cognitiveLevel"]["Trust"][-5:]
            },
            {
              "name":"Fear",
              "data":old_data["cognitiveLevel"]["Fear"][-5:]
            },
            {
              "name":"Surprise",
              "data":old_data["cognitiveLevel"]["Surprise"][-5:]
            },
            {
              "name":"Anger",
              "data":old_data["cognitiveLevel"]["Anger"][-5:]
            },
            {
              "name":"Disgust",
              "data":old_data["cognitiveLevel"]["Disgust"][-5:]
            }
          ]
        }
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# get user cognitive
@app.route("/user/get_cognitive", methods=["OPTIONS","get"])
def get_cognitive():
    try:
      JSON_FILE = 'data/user/' + request.args.get('userName') + '.json'
      with open(JSON_FILE, "r") as file:
        old_data = json.load(file)
        res = {
          "cognitive_level":[
            old_data["cognitiveLevel"]["Joy"][-1],
            old_data["cognitiveLevel"]["Trust"][-1],
            old_data["cognitiveLevel"]["Fear"][-1],
            old_data["cognitiveLevel"]["Surprise"][-1],
            old_data["cognitiveLevel"]["Anger"][-1],
            old_data["cognitiveLevel"]["Disgust"][-1]
          ],
          "tracingX":old_data["tracingX"][-5:],
          "tracingY":[
            {
              "name":"Engagement",
              "data":old_data["cognitiveLevel"]["Engagement"][-5:]
            },
            {
              "name":"Joy",
              "data":old_data["cognitiveLevel"]["Joy"][-5:]
            },
            {
              "name":"Trust",
              "data":old_data["cognitiveLevel"]["Trust"][-5:]
            },
            {
              "name":"Fear",
              "data":old_data["cognitiveLevel"]["Fear"][-5:]
            },
            {
              "name":"Surprise",
              "data":old_data["cognitiveLevel"]["Surprise"][-5:]
            },
            {
              "name":"Anger",
              "data":old_data["cognitiveLevel"]["Anger"][-5:]
            },
            {
              "name":"Disgust",
              "data":old_data["cognitiveLevel"]["Disgust"][-5:]
            }
          ]
        }
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
  
# get room info
@app.route("/room/get_room_info", methods=["OPTIONS","GET"])
def get_room_info():
  JSON_FILE = 'data/room/' + request.args.get('roomId') + '.json'
  print(JSON_FILE)
  if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as file:
        data = json.load(file)
    return jsonify(data), 200
  else:
    return jsonify({"error": "User not found"}), 404
  
# create room
@app.route("/room/create_room", methods=["POST"])
def create_room():
  data = request.get_json()
  if not data:
    return jsonify({"error": "Invalid data"}), 400
  try:
    roomId = generate_random_string(6)
    JSON_FILE = 'data/room/' + roomId + '.json'
    # if os.path.exists(JSON_FILE):
    #   return jsonify({"error": "Room is already exist"}), 200
    
    with open(JSON_FILE, "w") as file:
      new_json = {
        'roomId': roomId,
        'roomName': data['roomName'],
        'roomCustomName': data['roomCustomName'],
        'memberNum': data['memberNum'],
        'chatTime': data['chatTime'],
        'assertiveness': data['assertiveness'],
        'topic': data['topic'],
        'roomMember': [],
        'history': [
          {
            "userId":"u000",
            "userName":"Agent",
            "userAvatar":"/src/assets/Agent.PNG",
            "text":"Welcome everyone to today’s discussion. The topic we are discussing is '" + data['topic'] + "'Feel free to share your thoughts!",
            "time": datetime.now().strftime("%I:%M:%S %p"),
            "roomId": roomId
          }
        ]
      }
      json.dump(new_json, file, indent=2)
    return jsonify(new_json), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500
  
# join room
@app.route("/room/join_room", methods=["POST"])
def join_room_method():
  data = request.get_json()
  if not data:
    return jsonify({"error": "Invalid data"}), 400
  try:
    JSON_FILE = 'data/room/' +data['roomId'] + '.json'
    if os.path.exists(JSON_FILE):
      with open(JSON_FILE, "r") as file:
        old_data = json.load(file)
      roomMember = old_data['roomMember']
      for item in roomMember:
        if item['memberName'] == data['userName']:
          return jsonify({'success':'success'}), 200
      new_member = {
        "memberId": generate_random_string(4),
        "memberName": data["userName"],
        "memberAvatar": "/src/assets/"+data["userName"]+".JPG"
      }
      old_data['roomMember'].append(new_member)
      with open(JSON_FILE, 'w') as f:
        json.dump(old_data, f, ensure_ascii=False, indent=2)
      return jsonify({'success':'success'}), 200
    else:
      return jsonify({"error": "Room is not exist"}), 200
  except Exception as e:
        return jsonify({"error": str(e)}), 500
      
# 处理连接事件
@socketio.on('connect')
def handle_connect():
    print('A client connected.')

# 处理断开连接
@socketio.on('disconnect')
def handle_disconnect():
    print('A client disconnected.')
    
@socketio.on('join')
def handle_join(data):
    print(data)
    roomId = data['roomId']
    join_room(roomId)
    print(f"User {data['userName']} joined room {roomId}")

# 接收消息并广播
@socketio.on('send_message')
def handle_message(data):
    roomId = data["roomId"]
    emit('receive_message', data['message'], room=roomId)
    with lock:
      print(roomId)
      if roomId not in room_counters:
        room_counters[roomId] = 0
      save_message_to_json(data['message'])
      room_counters[roomId] += 1
      if room_counters[roomId] >= 4:
        send_system_message(roomId)
        
def send_system_message(roomId):
  # query llm api
  result= query_api(roomId)
  JSON_FILE = f'data/room/{roomId}.json'
  with open(JSON_FILE, "r") as file:
    old_data = json.load(file)
    msg = {
      "userId": "u000",
      "userName": "Agent",
      "userAvatar": "/src/assets/Agent.PNG",
      "text": result["response_content"],
      "time": datetime.now().strftime("%I:%M:%S %p"),
      "roomId": roomId
    }
    old_data["history"].append(msg)
    with open(JSON_FILE, 'w') as f:
      json.dump(old_data, f, ensure_ascii=False, indent=2)
    emit('receive_message', msg, room=roomId)
    room_counters[roomId] = 0

if __name__ == "__main__":
  socketio.run(app, host="0.0.0.0", port=5001, debug=True)