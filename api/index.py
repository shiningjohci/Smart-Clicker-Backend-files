from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import json
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app, 
     resources={r"/*": {
         "origins": ["https://shiningjohci.github.io"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"],
         "supports_credentials": True,
         "max_age": 86400
     }},
     supports_credentials=True)

# MongoDB连接
MONGODB_URI = os.environ.get('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.get_database('chrome_extension')
users_collection = db.users

# 全局CORS处理
@app.after_request
def after_request(response):
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    logger.debug(f"Response Headers before modification: {dict(response.headers)}")
    
    response.headers.add('Access-Control-Allow-Origin', 'https://shiningjohci.github.io')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    
    logger.debug(f"Response Headers after modification: {dict(response.headers)}")
    return response

# 处理OPTIONS请求
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    logger.debug(f"Handling OPTIONS request for path: {path}")
    response = jsonify({'status': 'ok'})
    return response, 200

# 根路由
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Chrome Extension API"}), 200

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    try:
        logger.debug("Processing registration request")
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
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    try:
        logger.debug("Processing login request")
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
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 检查VIP状态
@app.route('/api/check-vip', methods=['POST'])
def check_vip():
    try:
        logger.debug("Processing check-vip request")
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Missing username"}), 400
            
        user = users_collection.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"is_vip": user.get('is_vip', False)}), 200
        
    except Exception as e:
        logger.error(f"Check VIP error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 添加VIP状态
@app.route('/api/add-vip', methods=['POST'])
def add_vip():
    try:
        logger.debug("Processing add-vip request")
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Missing username"}), 400
            
        current_time = datetime.utcnow()
        # 默认VIP期限为30天
        vip_end_time = current_time + timedelta(days=30)
        
        # 创建新的VIP历史记录
        vip_record = {
            "action": "添加VIP",
            "timestamp": current_time,
            "end_time": vip_end_time
        }
        
        result = users_collection.update_one(
            {"username": username},
            {
                "$set": {
                    "is_vip": True,
                    "vip_start_time": current_time,
                    "vip_end_time": vip_end_time,
                    "updated_at": current_time
                },
                "$push": {
                    "vip_history": vip_record
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "message": "VIP status added successfully",
            "vip_details": {
                "start_time": current_time,
                "end_time": vip_end_time
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Add VIP error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 获取所有用户
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        logger.debug("Processing get users request")
        users = list(users_collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify({"users": users}), 200
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 删除用户
@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username):
    try:
        logger.debug(f"Processing delete user request for {username}")
        result = users_collection.delete_one({"username": username})
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 更新用户
@app.route('/api/users/<username>', methods=['PUT'])
def update_user(username):
    try:
        logger.debug(f"Processing update user request for {username}")
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
        logger.error(f"Update user error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 获取VIP详情
@app.route('/api/vip-details/<username>', methods=['GET'])
def get_vip_details(username):
    try:
        logger.debug(f"Processing get VIP details request for {username}")
        user = users_collection.find_one({"username": username})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # 获取或初始化VIP历史记录
        vip_history = user.get('vip_history', [])
        
        return jsonify({
            "username": username,
            "is_vip": user.get('is_vip', False),
            "vip_start_time": user.get('vip_start_time'),
            "vip_end_time": user.get('vip_end_time'),
            "vip_history": vip_history
        }), 200
        
    except Exception as e:
        logger.error(f"Get VIP details error: {str(e)}")
        return jsonify({"error": str(e)}), 500 