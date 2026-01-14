"""
文件上传相关路由
"""

from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
from auth.decorators import login_required

upload_bp = Blueprint('upload', __name__)

# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_FILE_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',  # 图片
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',  # 文档
    'txt', 'csv',  # 文本
    'zip', 'rar', '7z'  # 压缩包
}

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder, allowed_extensions):
    """保存上传的文件"""
    if not file or file.filename == '':
        return None, '没有选择文件'
    
    if not allowed_file(file.filename, allowed_extensions):
        return None, f'不允许的文件类型，允许的类型：{", ".join(allowed_extensions)}'
    
    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
    filename = secure_filename(filename)
    
    # 确保上传目录存在
    upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), upload_folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # 返回相对URL（需要包含/process前缀，因为前端通过代理访问）
    url = f"/process/uploads/{upload_folder}/{filename}"
    return url, None

@upload_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    """上传图片"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        url, error = save_file(file, 'images', ALLOWED_IMAGE_EXTENSIONS)
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'url': url,
                'name': file.filename
            }
        })
    except Exception as e:
        current_app.logger.error(f"上传图片失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '上传图片失败'
        }), 500

@upload_bp.route('/upload/file', methods=['POST'])
@login_required
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        url, error = save_file(file, 'files', ALLOWED_FILE_EXTENSIONS)
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'url': url,
                'name': file.filename
            }
        })
    except Exception as e:
        current_app.logger.error(f"上传文件失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '上传文件失败'
        }), 500

