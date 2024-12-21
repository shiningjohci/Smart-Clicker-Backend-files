from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import hashlib
import os
from pymongo import MongoClient
import json
import sys
import traceback

# 设置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app)

# 环境变量
MONGODB_URI = os.getenv('MONGODB_URI')
SECRET_KEY = os.getenv('JWT_SECRET')

# 记录环境变量状态（不记录具体值）
logger.info(f"MONGODB_URI is {'set' if MONGODB_URI else 'not set'}")
logger.info(f"JWT_SECRET is {'set' if SECRET_KEY else 'not set'}")

if not MONGODB_URI:
    logger.error("MONGODB_URI environment variable is not set")
    raise ValueError("MONGODB_URI environment variable is required")

if not SECRET_KEY:
    logger.error("JWT_SECRET environment variable is not set")
    raise ValueError("JWT_SECRET environment variable is required")

# 全局CORS处理
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

# 处理所有OPTIONS请求
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({}), 200

# MongoDB连接函数
def get_db_connection():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # 验证连接
        client.server_info()
        logger.info("MongoDB connection successful")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        raise

# 初始化MongoDB连接
try:
    client = get_db_connection()
    db = client.get_database('user_auth_db')
    users_collection = db.get_collection('users')
except Exception as e:
    logger.error(f"Failed to initialize MongoDB: {str(e)}")
    raise

# 新增：获取所有用户列表接口
@app.route('/auth/users', methods=['GET'])
def get_users():
    try:
        logger.info("Get users list endpoint accessed")
        
        # 验证token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return jsonify({'error': '未授权'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # 验证token并获取用户信息
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            requesting_user = users_collection.find_one({'username': payload['username']})
            
            if not requesting_user:
                logger.error(f"User not found: {payload['username']}")
                return jsonify({'error': '用户不存在'}), 404
                
            # 获取所有用户列表
            users = list(users_collection.find({}, {
                'password': 0  # 排除密码字段
            }))
            
            # 转换ObjectId为字符串
            for user in users:
                user['_id'] = str(user['_id'])
                
            logger.info(f"Successfully retrieved {len(users)} users")
            return jsonify({
                'users': users,
                'total': len(users)
            })
            
        except jwt.ExpiredSignatureError:
            logger.error("Token expired")
            return jsonify({'error': 'token已过期'}), 401
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return jsonify({'error': '无效的token'}), 401
            
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ... existing code ... 