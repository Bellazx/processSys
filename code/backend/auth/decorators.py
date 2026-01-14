"""
认证装饰器
"""

from functools import wraps
from flask import session, jsonify, current_app
from models import AdminConfig


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': '未登录，请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            
            # 检查是否为超级管理员
            admin = AdminConfig.query.filter_by(user_id=user_id).first()
            if admin and admin.is_super_admin:
                return f(*args, **kwargs)
            
            # 检查具体权限
            if permission == 'manage_form':
                # 超级管理员或类别管理员可以管理表单
                # 类别管理员通过CategoryAdmin表检查，这里先检查超级管理员和can_manage_form权限
                if not admin:
                    return jsonify({
                        'success': False,
                        'message': '无权限管理表单'
                    }), 403
                # 超级管理员可以管理所有表单
                if not admin.is_super_admin and not admin.can_manage_form:
                    # 如果不是超级管理员且没有can_manage_form权限，检查是否为类别管理员
                    # 类别管理员的权限检查在具体的业务逻辑中处理（因为需要知道是哪个类别）
                    return jsonify({
                        'success': False,
                        'message': '无权限管理表单'
                    }), 403
            elif permission == 'manage_external':
                if not admin or not admin.can_manage_external:
                    return jsonify({
                        'success': False,
                        'message': '无权限外派工单'
                    }), 403
            elif permission == 'super_admin':
                if not admin or not admin.is_super_admin:
                    return jsonify({
                        'success': False,
                        'message': '需要超级管理员权限'
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

