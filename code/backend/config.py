"""
审批系统配置文件
"""

import os


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'approval-system-secret-key-2025'
    
    # Session配置
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
    # Session Cookie配置 - 确保cookie可以跨路径传递
    SESSION_COOKIE_PATH = '/'  # 设置为根路径，确保所有路径都可以访问
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # 允许跨站请求携带cookie
    
    # SQL Server数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mssql+pyodbc://staff:Hr9rlZ4y@10.119.2.152:1433/staff?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # jAccount OAuth2/OIDC配置
    JACCOUNT_CLIENT_ID = os.environ.get('JACCOUNT_CLIENT_ID') or 'dqlj1Df3qSZGoO5zU8Ui'
    JACCOUNT_CLIENT_SECRET = os.environ.get('JACCOUNT_CLIENT_SECRET') or 'CE4FEC7FDC684FB30B19F2FBD34C585EE3CD83F7B35140B0'
    JACCOUNT_AUTHORIZATION_URL = 'https://jaccount.sjtu.edu.cn/oauth2/authorize'
    JACCOUNT_TOKEN_URL = 'https://jaccount.sjtu.edu.cn/oauth2/token'
    JACCOUNT_USERINFO_URL = 'https://api.sjtu.edu.cn/v1/me/profile'
    JACCOUNT_LOGOUT_URL = 'https://jaccount.sjtu.edu.cn/oauth2/logout'
    
    # 服务器IP地址配置（用于生成URL，可通过环境变量覆盖）
    _SERVER_IP = os.environ.get('SERVER_IP') or '10.119.9.223'
    _SERVER_PORT = os.environ.get('SERVER_PORT') or '80'
    _BACKEND_PORT = os.environ.get('BACKEND_PORT') or '8081'
    
    SERVER_IP = _SERVER_IP
    SERVER_PORT = _SERVER_PORT
    BACKEND_PORT = _BACKEND_PORT
    
    # 回调地址：使用标准的回调路径，由后端处理后再重定向到前端
    # jAccount会根据client_id和secretkey验证，不需要预先注册回调地址
    # 注意：回调路径是后端API路径，不需要包含/libProcess前缀
    JACCOUNT_REDIRECT_URI = os.environ.get('JACCOUNT_REDIRECT_URI') or f'http://{_SERVER_IP}:{_SERVER_PORT}/process/auth/callback'
    
    # 前端URL（用于生成工单详情链接）
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or f'http://{_SERVER_IP}:{_SERVER_PORT}/libProcess'
    # 后端URL（用于API调用）
    BACKEND_URL = os.environ.get('BACKEND_URL') or f'http://{_SERVER_IP}:{_BACKEND_PORT}'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 交我办通知接口配置
    # 注意：通知接口使用资源拥有者密码凭据许可(Resource Owner Password Credentials Grant)方式获取access_token
    # 需要scope为send_notification的令牌
    NOTIFICATION_ACCESS_TOKEN = os.environ.get('NOTIFICATION_ACCESS_TOKEN') or ''
    # 通知接口获取token使用的client_id和client_secret（使用jAccount的凭据）
    NOTIFICATION_CLIENT_ID = os.environ.get('NOTIFICATION_CLIENT_ID') or JACCOUNT_CLIENT_ID
    NOTIFICATION_CLIENT_SECRET = os.environ.get('NOTIFICATION_CLIENT_SECRET') or JACCOUNT_CLIENT_SECRET
    # 发送通知使用的账号和密码（用于密码凭据方式获取token）
    NOTIFICATION_ACCOUNT = os.environ.get('NOTIFICATION_ACCOUNT') or 'lib_it@sjtu.edu.cn'
    NOTIFICATION_PASSWORD = os.environ.get('NOTIFICATION_PASSWORD') or 'libit888bang'
    
    # 授权用户列表（空列表表示所有通过jAccount认证的用户都可访问）
    AUTHORIZED_USERS = []


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 回调地址：继承基础配置，或使用环境变量覆盖
    # jAccount会根据client_id和secretkey验证，不需要预先注册回调地址


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境使用环境变量中的SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'approval-system-secret-key-2025-production'
    # 注意：生产环境建议通过环境变量设置SECRET_KEY
    
    # 生产环境回调地址：使用环境变量或从基础配置继承
    _SERVER_IP = os.environ.get('SERVER_IP') or '10.119.9.223'
    _SERVER_PORT = os.environ.get('SERVER_PORT') or '80'
    JACCOUNT_REDIRECT_URI = os.environ.get('JACCOUNT_REDIRECT_URI') or f'http://{_SERVER_IP}:{_SERVER_PORT}/process/auth/callback'
    # 确保FRONTEND_URL以/结尾，避免Nginx的301重定向
    _FRONTEND_URL = os.environ.get('FRONTEND_URL') or f'http://{_SERVER_IP}:{_SERVER_PORT}/libProcess'
    FRONTEND_URL = _FRONTEND_URL if _FRONTEND_URL.endswith('/') else _FRONTEND_URL + '/'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

