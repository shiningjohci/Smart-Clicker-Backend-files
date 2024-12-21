# ... existing code ...

# 处理OPTIONS请求
@app.route('/auth/users', methods=['OPTIONS'])
def handle_options():
    response = jsonify({})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

# 新增：获取所有用户列表接口
@app.route('/auth/users', methods=['GET'])
def get_users():
    try:
        logger.info("Get users list endpoint accessed")
        
        # 添加CORS头
        response = None
        
        # 验证token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            response = jsonify({'error': '未授权'})
            response.status_code = 401
        else:
            token = auth_header.split(' ')[1]
            
            try:
                # 验证token并获取用户信息
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                requesting_user = users_collection.find_one({'username': payload['username']})
                
                if not requesting_user:
                    logger.error(f"User not found: {payload['username']}")
                    response = jsonify({'error': '用户不存在'})
                    response.status_code = 404
                else:
                    # 获取所有用户列表
                    users = list(users_collection.find({}, {
                        'password': 0  # 排除密码字段
                    }))
                    
                    # 转换ObjectId为字符串
                    for user in users:
                        user['_id'] = str(user['_id'])
                        
                    logger.info(f"Successfully retrieved {len(users)} users")
                    response = jsonify({
                        'users': users,
                        'total': len(users)
                    })
                    
            except jwt.ExpiredSignatureError:
                logger.error("Token expired")
                response = jsonify({'error': 'token已过期'})
                response.status_code = 401
            except jwt.InvalidTokenError:
                logger.error("Invalid token")
                response = jsonify({'error': '无效的token'})
                response.status_code = 401
                
        # 添加CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
            
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

# ... existing code ... 