from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import json
from datetime import datetime
from bson import ObjectId

# 初始化Flask应用
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://shiningjohci.github.io"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True
    }
})

# MongoDB连接
MONGODB_URI = os.environ.get('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.get_database('chrome_extension')
users_collection = db.users

# 全局CORS处理
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://shiningjohci.github.io')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

# 处理OPTIONS请求
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

# 根路由
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Chrome Extension API"}), 200

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
            
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400
            
        new_user = {
            "username": username,
            "password": password,  # 实际应用中应该加密
            "is_vip": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = users_collection.insert_one(new_user)
        return jsonify({"message": "User registered successfully", "user_id": str(result.inserted_id)}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
            
        user = users_collection.find_one({"username": username, "password": password})
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
            
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "is_vip": user.get('is_vip', False)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 检查VIP状态
@app.route('/api/check-vip', methods=['POST'])
def check_vip():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Missing username"}), 400
            
        user = users_collection.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"is_vip": user.get('is_vip', False)}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 添加VIP状态
@app.route('/api/add-vip', methods=['POST'])
def add_vip():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Missing username"}), 400
            
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"is_vip": True, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "User not found or already VIP"}), 404
            
        return jsonify({"message": "VIP status added successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取所有用户
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = list(users_collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify({"users": users}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 删除用户
@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username):
    try:
        result = users_collection.delete_one({"username": username})
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 更新用户
@app.route('/api/users/<username>', methods=['PUT'])
def update_user(username):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No update data provided"}), 400
            
        data['updated_at'] = datetime.utcnow()
        result = users_collection.update_one(
            {"username": username},
            {"$set": data}
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": "User updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 