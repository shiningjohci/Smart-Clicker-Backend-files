from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import hashlib
import os
from pymongo import MongoClient
from http.server import BaseHTTPRequestHandler

app = Flask(__name__)
CORS(app)

# 环境变量
MONGODB_URI = os.getenv('MONGODB_URI', 'your-mongodb-uri')
SECRET_KEY = os.getenv('JWT_SECRET', 'your-secret-key')

# 连接MongoDB
client = MongoClient(MONGODB_URI)
db = client.get_database('user_auth_db')
users_collection = db.get_collection('users')

# 根路由
@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'API is running'
    })

# 错误处理
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested URL was not found on the server'
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

# 生成JWT token
def generate_token(user_id, username):
    payload = {
        'user_id': str(user_id),
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# 验证密码
def verify_password(stored_password, provided_password):
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

# 注册接口
@app.route('/auth/register', methods=['POST'])
def register():
    try:
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
        
        return jsonify({
            'message': '注册成功',
            'username': username,
            'token': token
        })
    except Exception as e:
        app.logger.error(f'Registration error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# 登录接口
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        user = users_collection.find_one({'username': username})
        
        if user and verify_password(user['password'], password):
            token = generate_token(user['_id'], username)
            return jsonify({
                'message': '登录成功',
                'username': username,
                'token': token
            })
        else:
            return jsonify({'error': '用户名或密码错误'}), 401
    except Exception as e:
        app.logger.error(f'Login error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# 检查VIP状态接口
@app.route('/auth/check-vip', methods=['GET'])
def check_vip():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权'}), 401
        
        token = auth_header.split(' ')[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user = users_collection.find_one({'username': payload['username']})
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({
            'isVip': bool(user.get('is_vip', False))
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'token已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': '无效的token'}), 401
    except Exception as e:
        app.logger.error(f'VIP check error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# 添加VIP接口（测试用）
@app.route('/auth/add-vip/<username>', methods=['POST'])
def add_vip(username):
    try:
        result = users_collection.update_one(
            {'username': username},
            {'$set': {'is_vip': True}}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': f'已将用户 {username} 设置为VIP'})
        else:
            return jsonify({'error': '用户不存在'}), 404
    except Exception as e:
        app.logger.error(f'Add VIP error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# 测试路由
@app.route('/test')
def test_route():
    return jsonify({'message': 'Test route working!'})

# Vercel handler
def handler(request):
    if request.method == 'POST':
        # Handle POST request
        return app(request.environ, lambda x, y: y)
    elif request.method == 'GET':
        # Handle GET request
        return app(request.environ, lambda x, y: y)
    else:
        # Handle other methods
        return app(request.environ, lambda x, y: y)