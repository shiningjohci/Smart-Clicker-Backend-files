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

# 根路由
@app.route('/')
def index():
    try:
        # 测试MongoDB连接
        users_collection.find_one({})
        logger.info("Root route accessed, MongoDB connection test successful")
        return jsonify({
            'status': 'ok',
            'message': 'API is running'
        })
    except Exception as e:
        logger.error(f"Error in root route: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Database connection error',
            'error': str(e)
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(e):
    logger.error(f"404 error: {str(e)}")
    return jsonify({
        'error': 'Not found',
        'message': 'The requested URL was not found on the server'
    }), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

# 生成JWT token
def generate_token(user_id, username):
    try:
        payload = {
            'user_id': str(user_id),
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise

# 验证密码
def verify_password(stored_password, provided_password):
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

# 注册接口
@app.route('/auth/register', methods=['POST'])
def register():
    try:
        logger.info("Register endpoint accessed")
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        # 检查用户名是否已存在
        if users_collection.find_one({'username': username}):
            return jsonify({'error': '用户名已存在'}), 400
        
        # 对密码进行哈希处理
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 创建新用户
        user = {
            'username': username,
            'password': hashed_password,
            'is_vip': False,
            'created_at': datetime.datetime.utcnow()
        }
        result = users_collection.insert_one(user)
        
        # 生成token
        token = generate_token(result.inserted_id, username)
        
        logger.info(f"User registered successfully: {username}")
        return jsonify({
            'message': '注册成功',
            'username': username,
            'token': token
        })
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 登录接口
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        logger.info("Login endpoint accessed")
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        user = users_collection.find_one({'username': username})
        
        if user and verify_password(user['password'], password):
            token = generate_token(user['_id'], username)
            logger.info(f"User logged in successfully: {username}")
            return jsonify({
                'message': '登录成功',
                'username': username,
                'token': token
            })
        else:
            return jsonify({'error': '用户名或密码错误'}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 检查VIP状态接口
@app.route('/auth/check-vip', methods=['GET'])
def check_vip():
    try:
        logger.info("Check VIP endpoint accessed")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权'}), 401
        
        token = auth_header.split(' ')[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user = users_collection.find_one({'username': payload['username']})
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        is_vip = bool(user.get('is_vip', False))
        logger.info(f"VIP status checked for user {payload['username']}: {is_vip}")
        return jsonify({'isVip': is_vip})
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        return jsonify({'error': 'token已过期'}), 401
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return jsonify({'error': '无效的token'}), 401
    except Exception as e:
        logger.error(f"VIP check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 添加VIP接口（测试用）
@app.route('/auth/add-vip/<username>', methods=['POST'])
def add_vip(username):
    try:
        logger.info(f"Add VIP endpoint accessed for user: {username}")
        result = users_collection.update_one(
            {'username': username},
            {'$set': {'is_vip': True}}
        )
        
        if result.modified_count > 0:
            logger.info(f"VIP status added for user: {username}")
            return jsonify({'message': f'已将用户 {username} 设置为VIP'})
        else:
            return jsonify({'error': '用户不存在'}), 404
    except Exception as e:
        logger.error(f"Add VIP error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 测试路由
@app.route('/test')
def test_route():
    logger.info("Test route accessed")
    return jsonify({'message': 'Test route working!'})

# Remove the handler function and just export the app
app.debug = True

# Export the Flask app directly
app = app