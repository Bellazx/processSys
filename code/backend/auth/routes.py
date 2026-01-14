"""
认证路由
处理jAccount OAuth2/OIDC登录、登出、回调等
"""

from flask import Blueprint, request, jsonify, session, current_app, redirect
import logging
from sqlalchemy import text
from .jaccount_client import JAccountClient
from models import Staff, db

logger = logging.getLogger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/login', methods=['GET'])
def login():
    """
    获取登录URL
    返回jAccount授权URL
    """
    try:
        client = JAccountClient(current_app.config)
        state = request.args.get('state')
        auth_url, state = client.get_authorization_url(state)
        
        return jsonify({
            'success': True,
            'loginUrl': auth_url,
            'state': state
        })
    except Exception as e:
        logger.error(f"获取登录URL失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取登录URL失败'
        }), 500


@auth_bp.route('/auth/callback', methods=['GET'])
def callback():
    """
    OAuth2回调处理
    处理jAccount返回的授权码，获取token并解析用户信息
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.error(f"授权失败: {error}")
            return jsonify({
                'success': False,
                'message': f'授权失败: {error}'
            }), 400
        
        if not code:
            return jsonify({
                'success': False,
                'message': '缺少授权码'
            }), 400
        
        client = JAccountClient(current_app.config)
        
        # 获取token
        token_result = client.get_token(code)
        if not token_result['success']:
            logger.error(f"获取token失败: {token_result.get('message')}")
            return jsonify(token_result), 500
        
        token_data = token_result['data']
        access_token = token_data.get('access_token')
        id_token = token_data.get('id_token')  # ID token，包含type字段
        
        # 使用Profile API获取用户信息（因为scope是profile）
        profile_result = client.get_user_profile(access_token)
        if not profile_result['success']:
            logger.error(f"获取用户信息失败: {profile_result.get('message')}")
            return jsonify(profile_result), 500
        
        profile_data = profile_result['data']
        # Profile API返回的字段：account, name, code等
        # 优先使用code（学工号），如果没有则使用account（jAccount账号）
        user_id = profile_data.get('code') or profile_data.get('account') or profile_data.get('id')
        user_name = profile_data.get('name', user_id)  # 姓名
        
        logger.info(f"解析用户信息: user_id={user_id}, user_name={user_name}")
        
        # 确保user_id不为空
        if not user_id:
            logger.error("user_id为空，无法继续处理")
            return jsonify({
                'success': False,
                'message': '无法获取用户ID'
            }), 500
        
        # 从Profile API获取用户类型代码（userType字段）
        # Profile API返回格式：{'userType': 'faculty', 'userTypeName': '教职工'}
        user_type_code = profile_data.get('userType')
        user_type_name = profile_data.get('userTypeName')
        logger.info(f"从Profile API获取用户类型代码: userType={user_type_code}, userTypeName={user_type_name}")
        
        # 从staff表获取用户详细信息（使用cardno学工号匹配）
        # 注意：staff表的学工号字段是cardno，不是code
        staff = None
        # user_id可能是code（学工号）或account（jAccount账号）
        # 先尝试用code查找（因为Profile API返回的code是学工号）
        code = profile_data.get('code')
        if code:
            try:
                # 使用原生SQL查询，因为staff表的学工号字段是cardno
                sql = "SELECT id, name, cardno, depart, mobilephone, email, gender, status FROM staff WHERE cardno = :cardno AND status = '在职'"
                result = db.session.execute(text(sql), {'cardno': code})
                row = result.fetchone()
                if row:
                    # 构造staff对象（用于兼容现有代码）
                    class StaffObj:
                        def __init__(self, row_data):
                            self.id = row_data[0]
                            self.name = row_data[1]
                            self.cardno = row_data[2]
                            self.code = row_data[2]  # 兼容code属性
                            self.depart = row_data[3]
                            self.dept = row_data[3]  # 兼容dept属性
                            self.phone = row_data[4] if len(row_data) > 4 and row_data[4] else None
                            self.mobilephone = row_data[4] if len(row_data) > 4 and row_data[4] else None
                            self.email = row_data[5] if len(row_data) > 5 and row_data[5] else None
                            self.gender = row_data[6] if len(row_data) > 6 and row_data[6] else None
                            self.status = row_data[7] if len(row_data) > 7 and row_data[7] else None
                    staff = StaffObj(row)
                    logger.info(f"使用cardno={code}查找staff: 找到")
                else:
                    logger.info(f"使用cardno={code}查找staff: 未找到")
            except Exception as e:
                logger.warning(f"查询staff表失败: {e}，使用Profile API信息")
        
        # 如果没找到，尝试用user_id查找
        if not staff and user_id:
            try:
                sql = "SELECT id, name, cardno, depart, mobilephone, email, gender, status FROM staff WHERE cardno = :cardno AND status = '在职'"
                result = db.session.execute(text(sql), {'cardno': user_id})
                row = result.fetchone()
                if row:
                    class StaffObj:
                        def __init__(self, row_data):
                            self.id = row_data[0]
                            self.name = row_data[1]
                            self.cardno = row_data[2]
                            self.code = row_data[2]  # 兼容code属性
                            self.depart = row_data[3]
                            self.dept = row_data[3]  # 兼容dept属性
                            self.phone = row_data[4] if len(row_data) > 4 and row_data[4] else None
                            self.mobilephone = row_data[4] if len(row_data) > 4 and row_data[4] else None
                            self.email = row_data[5] if len(row_data) > 5 and row_data[5] else None
                            self.gender = row_data[6] if len(row_data) > 6 and row_data[6] else None
                            self.status = row_data[7] if len(row_data) > 7 and row_data[7] else None
                    staff = StaffObj(row)
                    logger.info(f"使用cardno={user_id}查找staff: 找到")
                else:
                    logger.info(f"使用cardno={user_id}查找staff: 未找到")
            except Exception as e:
                logger.warning(f"查询staff表失败: {e}")
        
        if staff:
            user_name = staff.name or user_name
            user_dept = staff.dept
            # 优先使用staff表的mobilephone，如果为空则尝试从Profile API获取
            user_phone = staff.mobilephone or profile_data.get('mobile')
            user_email = staff.email or profile_data.get('email')
            logger.info(f"从staff表获取信息: {user_name}, {user_dept}, phone={user_phone}, email={user_email}")
        else:
            # 使用Profile API返回的信息
            user_dept = profile_data.get('organize', {}).get('name') if profile_data.get('organize') else None
            user_phone = profile_data.get('mobile')
            user_email = profile_data.get('email')
            logger.info(f"使用Profile API信息: dept={user_dept}, phone={user_phone}, email={user_email}")
            logger.info(f"Profile API完整数据: {profile_data}")
        
        if not user_type_code:
            logger.warning("未能从Profile API获取用户类型代码（userType字段）")
        
        # 检查用户权限
        authorized_users = current_app.config.get('AUTHORIZED_USERS', [])
        if authorized_users and user_id not in authorized_users:
            logger.warning(f"用户 {user_id} 无权限访问系统")
            return jsonify({
                'success': False,
                'message': '用户无权限访问系统'
            }), 403
        
        # 设置session
        try:
            session['user_id'] = user_id
            session['user_name'] = user_name
            session['user_dept'] = user_dept
            session['user_phone'] = user_phone
            session['user_email'] = user_email
            session['user_type_code'] = user_type_code  # 用户类型代码（faculty, student等）
            session['access_token'] = access_token
            session['refresh_token'] = token_data.get('refresh_token')
            
            # 确保session保存
            session.permanent = True
            
            logger.info(f"用户 {user_id} ({user_name}) 登录成功，session已设置，用户类型: {user_type_code}")
            logger.info(f"Session keys: {list(session.keys())}")
        except Exception as e:
            logger.error(f"设置session失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'设置session失败: {str(e)}'
            }), 500
        
        # 重定向到前端首页（清除URL参数）
        try:
            # 根据请求的Host动态生成前端URL，而不是使用配置文件中硬编码的IP
            # 优先使用X-Forwarded-Host（Nginx传递的原始Host），其次使用Host头
            request_host = request.headers.get('X-Forwarded-Host') or request.headers.get('Host', '')
            
            if request_host:
                # 获取请求协议（优先使用X-Forwarded-Proto，因为可能经过Nginx代理）
                scheme = request.headers.get('X-Forwarded-Proto') or request.scheme
                
                # 构建前端URL，使用/libProcess路径
                # 如果Host包含端口（如开发环境3003），保留端口
                frontend_url = f"{scheme}://{request_host}/libProcess"
            else:
                # 如果无法获取Host，使用配置中的FRONTEND_URL
                frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3003/libProcess')
            
            logger.info(f"重定向到前端: {frontend_url}?login=success (请求Host: {request_host}, Scheme: {scheme if request_host else 'N/A'})")
            return redirect(f"{frontend_url}?login=success")
        except Exception as e:
            logger.error(f"重定向失败: {e}", exc_info=True)
            # 如果重定向失败，返回JSON响应
            return jsonify({
                'success': True,
                'user_id': user_id,
                'user_name': user_name,
                'user_dept': user_dept,
                'message': '登录成功，请刷新页面'
            })
    except Exception as e:
        logger.error(f"登录回调处理失败: {e}", exc_info=True)
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'登录处理失败: {str(e)}'
        }), 500


@auth_bp.route('/auth/user/info', methods=['GET'])
def get_user_info():
    """
    获取当前登录用户信息（包含权限信息）
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '未登录'
        }), 401
    
    user_id = session.get('user_id')
    
    # 获取用户权限信息
    from models import AdminConfig, CategoryAdmin
    admin = AdminConfig.query.filter_by(user_id=user_id).first()
    
    # 检查是否为类别管理员
    category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
    is_category_admin = len(category_admins) > 0
    managed_category_ids = [ca.category_id for ca in category_admins] if is_category_admin else []
    
    # 确定用户身份类型
    is_super_admin = admin and admin.is_super_admin
    if is_super_admin:
        user_type = 'super_admin'
    elif is_category_admin:
        user_type = 'category_admin'
    else:
        user_type = 'normal'
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': session.get('user_id'),
            'user_name': session.get('user_name'),
            'user_dept': session.get('user_dept'),
            'user_phone': session.get('user_phone'),
            'user_email': session.get('user_email'),
            'user_type_code': session.get('user_type_code'),  # 用户类型代码（faculty, student等）
            'user_type': user_type,  # 用户身份类型（normal/category_admin/super_admin）
            # 权限信息
            'is_super_admin': is_super_admin,
            'can_manage_form': is_super_admin or (admin and admin.can_manage_form) if admin else False,
            'can_manage_external': admin.can_manage_external if admin else False,
            'is_category_admin': is_category_admin,
            'managed_category_ids': managed_category_ids
        }
    })


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """
    登出接口
    清除session并返回jAccount登出URL
    
    根据jAccount文档，登出流程：
    1. 调用此接口获取jAccount登出URL
    2. 前端跳转到jAccount登出页面
    3. jAccount登出完成后，重定向到post_logout_redirect_uri（前端登录页）
    """
    try:
        user_id = session.get('user_id')
        
        # 获取登出URL
        client = JAccountClient(current_app.config)
        
        # 从请求中获取重定向地址（可选）
        # 如果前端指定了redirect_uri，使用它；否则使用默认值（前端登录页）
        post_logout_redirect_uri = None
        if request.is_json and request.json:
            post_logout_redirect_uri = request.json.get('redirect_uri')
        elif request.args:
            post_logout_redirect_uri = request.args.get('redirect_uri')
        
        # 生成state参数（用于防止CSRF攻击）
        import secrets
        state = secrets.token_urlsafe(32)
        
        # 获取登出URL
        logout_url = client.get_logout_url(post_logout_redirect_uri, state)
        
        # 清除session（在跳转到jAccount登出页面前清除本地session）
        session.clear()
        
        logger.info(f"用户 {user_id} 登出，生成登出URL: {logout_url}")
        
        return jsonify({
            'success': True,
            'logoutUrl': logout_url,
            'state': state,
            'message': '登出成功'
        })
    except Exception as e:
        logger.error(f"登出失败: {e}", exc_info=True)
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'登出失败: {str(e)}'
        }), 500


@auth_bp.route('/auth/logout/callback', methods=['GET'])
def logout_callback():
    """
    登出回调处理
    当jAccount登出完成后，会重定向到此地址（post_logout_redirect_uri）
    此接口主要用于处理state参数验证（可选）
    
    注意：jAccount可能会使用&而不是?来追加参数，所以需要兼容处理
    """
    try:
        # 兼容处理URL格式：可能是 ?state=... 或 &state=...
        # 如果URL中包含&state=，说明格式有问题，需要从request.url中提取
        state = request.args.get('state')
        error = request.args.get('error')
        
        # 如果从args中获取不到state，尝试从URL中提取（处理&格式）
        if not state:
            import re
            url_match = re.search(r'[&?]state=([^&]*)', request.url)
            if url_match:
                state = url_match.group(1)
                logger.info(f"从URL中提取state参数: {state}")
        
        if error:
            logger.warning(f"jAccount登出回调错误: {error}")
        
        logger.info(f"登出回调收到请求: state={state}, error={error}, URL={request.url}")
        
        # 确保session已清除（双重保险）
        session.clear()
        
        # 重定向到前端登录页
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3003')
        logger.info(f"登出回调处理完成，重定向到: {frontend_url}/login")
        
        from flask import redirect
        return redirect(f"{frontend_url}/login?logout=success")
    except Exception as e:
        logger.error(f"登出回调处理失败: {e}", exc_info=True)
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        # 即使回调处理失败，也重定向到登录页
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3003')
        from flask import redirect
        return redirect(f"{frontend_url}/login")

