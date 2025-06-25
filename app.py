from flask import Flask, request, jsonify, current_app
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
from database import connect_database
from bson import ObjectId
from agent_utils import get_student_agent_response, get_teacher_response

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")
lock = Lock()

# database connection
app.user_collection, app.room_collection = connect_database()

room_counters = {}

# agent related
student_client = OpenAI(
    api_key="gpustack_dca95d48986a6f0c_b597d9343202a28c4d57a14026631130",
    base_url="http://159.223.84.150:9000/v1"
)
student_model_name = "llama3-70b-instruct-fp16"

teacher_client = client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
teacher_model_name = "QIHAO-8B"


def generate_random_string(length):
    # 定义字符集合，包括大小写字母和数字
    characters = string.ascii_letters + string.digits
    # 从字符集合中随机选择指定数量的字符
    return "".join(random.choices(characters, k=length))


@app.route("/")
def home():
    return "Welcome to the Flask Backend!"


# register
@app.route("/user/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    try:
        image_paths = [
            "/src/assets/Bob.JPG",
            "/src/assets/ALice.JPG",
            "/src/assets/Jim.JPG",
            "/src/assets/Jack.JPG",
            "/src/assets/David.JPG",
        ]
        userAvatar = random.choice(image_paths)
        user_info = {
            "userName": data["userName"],
            "userPswd": data["userPswd"],
            "mode": data["mode"],
            "userAvatar": userAvatar,
            "cognitiveLevel": {
                "Joy": [0],
                "Trust": [0],
                "Fear": [0],
                "Surprise": [0],
                "Anger": [0],
                "Disgust": [0],
                "Engagement": [0],
            },
            "tracingX": [0],
            "profile": {},
            "roomList": [],
        }
        result = current_app.user_collection.insert_one(user_info)
        return (
            jsonify(
                {
                    "status": "success",
                    "userId": str(result.inserted_id),
                    "mode": data["mode"],
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# login
@app.route("/user/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    try:
        users = list(current_app.user_collection.find({"userName": data["userName"]}))
        if len(users) <= 0:
            return jsonify({"error": "User does not exist!"}), 500
        else:
            for user in users:
                if user["userPswd"] == data["userPswd"]:
                    return (
                        jsonify(
                            {
                                "status": "success",
                                "userId": str(user["_id"]),
                                "mode": user["mode"],
                            }
                        ),
                        200,
                    )
            return jsonify({"error": "wrong password"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# get user info
@app.route("/user/get_user_info", methods=["OPTIONS", "GET"])
def get_user_info():
    userId = request.args.get("userId")
    try:
        user_query_result = current_app.user_collection.find_one(
            {"_id": ObjectId(userId)}
        )
        roomList = user_query_result["roomList"]
        userName = user_query_result["userName"]
        userAvatar = user_query_result["userAvatar"]
        return jsonify(
            {
                "userId": userId,
                "userName": userName,
                "userAvatar": userAvatar,
                "roomList": roomList,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# update user cogitive
@app.route("/user/update_cognitive", methods=["OPTIONS", "get"])
def update_cognitive():
    userId = request.args.get("userId")
    try:
        update_query = {
            "$push": {
                "cognitiveLevel.Joy": round(random.random(), 2),
                "cognitiveLevel.Trust": round(random.random(), 2),
                "cognitiveLevel.Fear": round(random.random(), 2),
                "cognitiveLevel.Surprise": round(random.random(), 2),
                "cognitiveLevel.Anger": round(random.random(), 2),
                "cognitiveLevel.Disgust": round(random.random(), 2),
                "cognitiveLevel.Engagement": round(random.random(), 2),
                "tracingX": datetime.now().strftime("%I:%M:%S %p"),
            }
        }
        user_update_result = current_app.user_collection.update_one(
            {"_id": ObjectId(userId)}, update_query
        )
        try:
            user_query_result = current_app.user_collection.find_one(
                {"_id": ObjectId(userId)}
            )
            res = {
                "cognitive_level": [
                    user_query_result["cognitiveLevel"]["Joy"][-1],
                    user_query_result["cognitiveLevel"]["Trust"][-1],
                    user_query_result["cognitiveLevel"]["Fear"][-1],
                    user_query_result["cognitiveLevel"]["Surprise"][-1],
                    user_query_result["cognitiveLevel"]["Anger"][-1],
                    user_query_result["cognitiveLevel"]["Disgust"][-1],
                ],
                "tracingX": user_query_result["tracingX"][-5:],
                "tracingY": [
                    {
                        "name": "Engagement",
                        "data": user_query_result["cognitiveLevel"]["Engagement"][-5:],
                    },
                    {
                        "name": "Joy",
                        "data": user_query_result["cognitiveLevel"]["Joy"][-5:],
                    },
                    {
                        "name": "Trust",
                        "data": user_query_result["cognitiveLevel"]["Trust"][-5:],
                    },
                    {
                        "name": "Fear",
                        "data": user_query_result["cognitiveLevel"]["Fear"][-5:],
                    },
                    {
                        "name": "Surprise",
                        "data": user_query_result["cognitiveLevel"]["Surprise"][-5:],
                    },
                    {
                        "name": "Anger",
                        "data": user_query_result["cognitiveLevel"]["Anger"][-5:],
                    },
                    {
                        "name": "Disgust",
                        "data": user_query_result["cognitiveLevel"]["Disgust"][-5:],
                    },
                ],
            }
            return jsonify(res), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# get user cognitive
@app.route("/user/get_cognitive", methods=["OPTIONS", "get"])
def get_cognitive():
    userId = request.args.get("userId")
    try:
        user_query_result = current_app.user_collection.find_one(
            {"_id": ObjectId(userId)}
        )
        res = {
            "cognitive_level": [
                user_query_result["cognitiveLevel"]["Joy"][-1],
                user_query_result["cognitiveLevel"]["Trust"][-1],
                user_query_result["cognitiveLevel"]["Fear"][-1],
                user_query_result["cognitiveLevel"]["Surprise"][-1],
                user_query_result["cognitiveLevel"]["Anger"][-1],
                user_query_result["cognitiveLevel"]["Disgust"][-1],
            ],
            "tracingX": user_query_result["tracingX"][-5:],
            "tracingY": [
                {
                    "name": "Engagement",
                    "data": user_query_result["cognitiveLevel"]["Engagement"][-5:],
                },
                {
                    "name": "Joy",
                    "data": user_query_result["cognitiveLevel"]["Joy"][-5:],
                },
                {
                    "name": "Trust",
                    "data": user_query_result["cognitiveLevel"]["Trust"][-5:],
                },
                {
                    "name": "Fear",
                    "data": user_query_result["cognitiveLevel"]["Fear"][-5:],
                },
                {
                    "name": "Surprise",
                    "data": user_query_result["cognitiveLevel"]["Surprise"][-5:],
                },
                {
                    "name": "Anger",
                    "data": user_query_result["cognitiveLevel"]["Anger"][-5:],
                },
                {
                    "name": "Disgust",
                    "data": user_query_result["cognitiveLevel"]["Disgust"][-5:],
                },
            ],
        }
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# get room info
@app.route("/room/get_room_info", methods=["OPTIONS", "GET"])
def get_room_info():
    room_id = request.args.get("roomId")
    try:
        room_query_result = current_app.room_collection.find_one(
            {"_id": ObjectId(room_id)}
        )
        room_query_result["_id"] = str(room_query_result["_id"])
        return jsonify(room_query_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/room/create_room", methods=["POST"])
def create_room():
    REQUIRED_FIELDS = ["roomName", "memberNum", "chatTime", "topic"]

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    # 验证必需字段
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        current_time = datetime.now()
        room_info = {
            # 从data中获取的字段
            "roomName": data["roomName"],
            "roomCustomName": data.get("roomCustomName", ""),
            "memberNum": data["memberNum"],
            "chatTime": data["chatTime"],
            "assertiveness": data.get("assertiveness", 0.5),
            "topic": data["topic"],
            # 系统生成的字段
            "stage_id": "stage1",
            "start_i": 0,
            "roomMember": [],
            "history": [
                {
                    "date": current_time.strftime("%Y/%m/%d"),
                    "time": current_time.strftime("%H:%M:%S"),
                    "role_id": "T",
                    "name": "teacher",
                    "response": f'Welcome! Today\'s topic is "{data["topic"]}".The entire discussion process should try to follow the five stages of problem definition, exploration, integration, resolution and feedback. Please brainstorm and express your opinions!',
                }
            ],
        }

        # 插入数据库
        result = current_app.room_collection.insert_one(room_info)

        return (
            jsonify(
                {
                    "status": "success",
                    "roomId": str(result.inserted_id),
                    "roomName": room_info["roomName"],
                }
            ),
            201,
        )  # 使用201 Created状态码

    except Exception as e:
        app.logger.error(f"Room creation failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/room/get_agent_message", methods=["POST"])
def get_agent_message():
    data = request.get_json()
    try:
        room_info = current_app.room_collection.find_one(
            {"_id": ObjectId(data["room_id"])}
        )
        user_info = current_app.user_collection.find_one(
            {"_id": ObjectId(data["user_id"])}
        )
        status, student_response_json = get_student_agent_response(
            student_client, user_info, room_info, student_model_name, cut_word_length=18000
        )
        if status == "success":
            return student_response_json, 200
        elif "status" == "role_error":
            # add error student to student_errors
            try:
                room_update_result = current_app.room_collection.update_one(
                    {"_id": ObjectId(data["room_id"])},
                    {"$push": {"student_errors": student_response_json}},
                )
                return jsonify({"error": "AI agent cannot work now!"}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "system error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# join room
@app.route("/room/join_room", methods=["POST"])
def join_room_method():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    try:
        # JSON_FILE = "data/room/" + data["roomId"] + ".json"
        roomId = data["roomId"]
        userId = data["userId"]
        userName = data["userName"]
        userAvatar = data["userAvatar"]
        # query room member
        room_query_result = current_app.room_collection.find_one(
            {"_id": ObjectId(roomId)}
        )
        for member in room_query_result["roomMember"]:
            if member["memberId"] == userId:
                return (
                    jsonify(
                        {
                            "status": "success",
                            "roomId": roomId,
                            "userId": userId,
                            "userName": userName,
                        }
                    ),
                    200,
                )
        room_member_item = {
            "memberId": userId,
            "memberName": userName,
            "memberAvatar": userAvatar,
        }
        try:
            room_update_result = current_app.room_collection.update_one(
                {"_id": ObjectId(roomId)},
                {"$push": {"roomMember": room_member_item}},
            )
            user_update_result = current_app.user_collection.update_one(
                {"_id": ObjectId(userId)},
                {
                    "$push": {
                        "roomList": {
                            "roomId": roomId,
                            "roomName": room_query_result["roomName"],
                        }
                    }
                },
            )
            return (
                jsonify(
                    {
                        "status": "success",
                        "roomId": roomId,
                        "userId": userId,
                        "userName": userName,
                    }
                ),
                200,
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 处理连接事件
@socketio.on("connect")
def handle_connect():
    print("A client connected.")


# 处理断开连接
@socketio.on("disconnect")
def handle_disconnect():
    print("A client disconnected.")


@socketio.on("join")
def handle_join(data):
    print(data)
    roomId = data["roomId"]
    join_room(roomId)
    print(f"User {data['userName']} joined room {roomId}")


# 接收消息并广播
@socketio.on("send_message")
def handle_message(data):
    userName = data["userName"]
    roomId = data["roomId"]
    message = data["message"]
    with lock:
        room_info = current_app.room_collection.find_one({"_id": ObjectId(roomId)})
        room_info["_id"] = str(room_info["_id"])
        status, teacher_res = get_teacher_response(
            teacher_client, userName, message, room_info, teacher_model_name, cut_word_length=18000
        )
        if status == "intervention_no":
            append_result_student = current_app.room_collection.update_one(
                {"_id": ObjectId(roomId)}, {"$push": {"history": teacher_res}}
            )
            emit("receive_message", data["message"], room=roomId)
        else:
            append_result_student = current_app.room_collection.update_one(
                {"_id": ObjectId(roomId)}, {"$push": {"history": message}}
            )
            emit("receive_message", data["message"], room=roomId)
            append_result_teacher = current_app.room_collection.update_one(
                {"_id": ObjectId(roomId)}, {"$push": {"history": teacher_res}}
            )
            emit("receive_message", teacher_res, room=roomId)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
