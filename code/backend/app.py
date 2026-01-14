"""
图书馆审批系统后端应用
集成jAccount OAuth2/OIDC认证和工单管理功能
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
from datetime import datetime
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 加载配置
from config import config
config_name = os.environ.get('FLASK_ENV', 'development')
# 确保使用有效的配置
if config_name not in config:
    config_name = 'development'
app.config.from_object(config[config_name])

# 初始化扩展
CORS(app, supports_credentials=True)
Session(app)

# 初始化数据库
from models import db
db.init_app(app)

# 导入并注册蓝图
from auth.routes import auth_bp
from work_order.routes import work_order_bp
from form_config.routes import form_config_bp
from admin.routes import admin_bp
from notification.service import notification_bp
from upload.routes import upload_bp

app.register_blueprint(auth_bp, url_prefix='/process')
app.register_blueprint(work_order_bp, url_prefix='/process')
app.register_blueprint(form_config_bp, url_prefix='/process')
app.register_blueprint(admin_bp, url_prefix='/process')
app.register_blueprint(notification_bp, url_prefix='/process')
app.register_blueprint(upload_bp, url_prefix='/process')

# ============= 错误处理 =============

@app.errorhandler(401)
def unauthorized(error):
    return {'success': False, 'message': '未授权，请先登录'}, 401

@app.errorhandler(403)
def forbidden(error):
    return {'success': False, 'message': '权限不足'}, 403

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}", exc_info=True)
    return {'success': False, 'message': '服务器内部错误'}, 500

# ============= 数据库初始化 =============

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        logger.info("数据库表创建成功")

# ============= 健康检查 =============

@app.route('/process/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return {'success': True, 'message': '服务运行正常'}, 200

# ============= 静态文件服务 =============

@app.route('/process/uploads/<path:folder>/<path:filename>')
def uploaded_file(folder, filename):
    """提供上传文件的访问"""
    try:
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, folder, filename)
        
        # 安全检查：确保文件在uploads目录下
        upload_folder_abs = os.path.abspath(upload_folder)
        file_path_abs = os.path.abspath(file_path)
        
        if not file_path_abs.startswith(upload_folder_abs):
            logger.warning(f"非法文件访问尝试: {file_path}")
            return {'success': False, 'message': '文件不存在'}, 404
        
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return {'success': False, 'message': '文件不存在'}, 404
        
        return send_from_directory(
            os.path.join(upload_folder, folder),
            filename
        )
    except Exception as e:
        logger.error(f"提供文件失败: {e}", exc_info=True)
        return {'success': False, 'message': '文件访问失败'}, 500

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 运行应用
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=app.config['DEBUG']
    )

