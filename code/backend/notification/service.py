"""
交我办通知服务
对接交我办的通知接口，发送短信、邮件或交我办通知
接口文档：https://developer.sjtu.edu.cn/api/notification.html
"""

import requests
import logging
from flask import Blueprint, jsonify, request, current_app, session

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)


def extract_jaccount_from_email(email):
    """
    从email中提取jAccount账号（@字符之前的部分）
    
    Args:
        email: 邮箱地址，例如 "username@sjtu.edu.cn"
        
    Returns:
        str: jAccount账号，例如 "username"，如果email无效则返回None
    """
    if not email or '@' not in email:
        return None
    return email.split('@')[0]


class NotificationService:
    """通知服务类"""
    
    def __init__(self, config):
        self.config = config  # 保存配置引用
        self.api_base_url = 'https://api.sjtu.edu.cn/v1'
        # 需要从session或配置中获取access_token
        # 注意：通知接口需要使用客户端凭据授予方式获取access_token
    
    def _get_access_token(self):
        """
        获取访问令牌
        使用资源拥有者密码凭据许可(Resource Owner Password Credentials Grant)方式获取token
        """
        # 优先使用配置的access_token
        if isinstance(self.config, dict):
            access_token = self.config.get('NOTIFICATION_ACCESS_TOKEN', '')
        else:
            access_token = getattr(self.config, 'NOTIFICATION_ACCESS_TOKEN', '')
        
        if access_token:
            return access_token
        
        # 如果没有配置access_token，使用密码凭据方式自动获取
        try:
            from auth.token_client import TokenClient
            token_client = TokenClient(self.config)
            token_result = token_client.get_token(scope='send_notification')
            
            if token_result['success']:
                # 将token保存到配置中（可选：可以缓存到session或redis）
                access_token = token_result['access_token']
                # 注意：这里只是临时使用，建议配置NOTIFICATION_ACCESS_TOKEN环境变量
                # 或者保存refresh_token以便后续刷新
                logger.info("成功通过密码凭据方式获取通知接口access_token")
                return access_token
            else:
                logger.warning(f"无法获取access_token: {token_result.get('message')}")
                return ''
        except Exception as e:
            logger.error(f"获取access_token失败: {e}", exc_info=True)
            return ''
    
    def send_notification(self, notification_data):
        """
        发送通知（根据交我办通知接口规范）
        
        Args:
            notification_data: 通知数据字典，包含以下字段：
                - name: 标题
                - content: 正文（纯文本）
                - html: 正文（HTML格式，可选）
                - abstract: 正文摘要（可选）
                - app: App对象（可选）
                - phones: 手机号列表（可选）
                - emails: 邮箱列表（可选）
                - accounts: jAccount账号列表（可选）
                - users: 用户列表（可选）
                - channels: 发送渠道列表（必填），支持：email, sms, app, wechat_template
                
        Returns:
            dict: 发送结果
        """
        access_token = self._get_access_token()
        if not access_token:
            logger.warning("通知API access_token未配置，跳过发送")
            return {
                'success': False,
                'message': '通知API access_token未配置'
            }
        
        try:
            url = f"{self.api_base_url}/notification?access_token={access_token}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.put(
                url,
                json=notification_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('errno') == 0:
                logger.info(f"通知发送成功: {notification_data.get('name')}")
                return {
                    'success': True,
                    'message': '通知发送成功',
                    'data': result.get('entities', [{}])[0] if result.get('entities') else {}
                }
            else:
                error_msg = result.get('error', '未知错误')
                logger.error(f"通知发送失败: {error_msg}")
                return {
                    'success': False,
                    'message': f'通知发送失败: {error_msg}'
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"通知发送失败: {e}")
            return {
                'success': False,
                'message': f'通知发送失败: {str(e)}'
            }
    
    def send_to_account(self, account, title, content, channels=None, app_data=None):
        """
        发送通知给jAccount账号（便捷方法）
        
        Args:
            account: jAccount账号（从email中提取，@字符之前的部分）
            title: 通知标题
            content: 通知内容
            channels: 发送渠道列表，默认['app']
            app_data: App对象数据（可选）
            
        Returns:
            dict: 发送结果
        """
        if channels is None:
            channels = ['app']
        
        notification_data = {
            'name': title,
            'content': content,
            'accounts': [account],
            'channels': channels
        }
        
        if app_data:
            notification_data['app'] = app_data
        
        return self.send_notification(notification_data)
    
    def send_to_phone(self, phone, content, abstract=None):
        """
        发送短信通知（便捷方法）
        
        Args:
            phone: 手机号
            content: 短信内容
            abstract: 摘要（可选，优先级高于content）
            
        Returns:
            dict: 发送结果
        """
        notification_data = {
            'phones': [phone],
            'channels': ['sms']
        }
        
        if abstract:
            notification_data['abstract'] = abstract
        else:
            notification_data['content'] = content
        
        return self.send_notification(notification_data)
    
    def send_to_email(self, email, title, content, html=None):
        """
        发送邮件通知（便捷方法）
        
        Args:
            email: 邮箱地址
            title: 邮件标题
            content: 邮件正文（纯文本）
            html: 邮件正文（HTML格式，可选）
            
        Returns:
            dict: 发送结果
        """
        notification_data = {
            'name': title,
            'emails': [email],
            'channels': ['email']
        }
        
        if html:
            notification_data['html'] = html
        else:
            notification_data['content'] = content
        
        return self.send_notification(notification_data)
    
    def send_work_order_notification(self, order_no, action, order_url=None, 
                                     phone=None, email=None, applicant_name=None, category_name=None):
        """
        发送工单通知（专用方法，同时发送交我办通知和邮件通知）
        
        Args:
            order_no: 工单编号
            action: 操作类型（new/approved/rejected/returned/completed/transferred）
            order_url: 工单详情链接（可选）
            phone: 手机号（必填，用于sms渠道）
            email: 邮箱（必填，用于email渠道和提取jAccount账号）
            applicant_name: 申请人姓名（可选，用于通知内容）
            category_name: 工单类别名称（可选，用于通知内容）
            
        Returns:
            dict: 发送结果
        """
        action_map = {
            'new': ('新工单待审批', '您有新的工单待审批'),
            'approved': ('工单审批通过', '您的工单已通过审批'),
            'rejected': ('工单审批拒绝', '您的工单已被拒绝'),
            'returned': ('工单已打回', '您的工单已打回，请修改后重新提交'),
            'completed': ('工单已完成', '您的工单已完成'),
            'transferred': ('工单已转派', '工单已转派给您审批')
        }
        
        title, base_content = action_map.get(action, ('工单通知', f'工单 {order_no} 状态更新'))
        
        # 获取前端URL（用于生成系统首页链接）
        if isinstance(self.config, dict):
            frontend_url = self.config.get('FRONTEND_URL')
        else:
            frontend_url = getattr(self.config, 'FRONTEND_URL')
        
        # 构建纯文本通知内容（用于app通知）
        if applicant_name and category_name:
            # 同时有申请人姓名和工单类别
            if action == 'new':
                plain_content = f'{applicant_name} 提交的工单 {order_no}（类别：{category_name}）需要您审批'
            elif action == 'transferred':
                plain_content = f'工单 {order_no}（类别：{category_name}，申请人：{applicant_name}）已转派给您审批'
            else:
                plain_content = f'{base_content}：工单 {order_no}（类别：{category_name}，申请人：{applicant_name}）'
        elif applicant_name:
            # 只有申请人姓名
            if action == 'new':
                plain_content = f'{applicant_name} 提交的工单 {order_no} 需要您审批'
            elif action == 'transferred':
                plain_content = f'工单 {order_no}（申请人：{applicant_name}）已转派给您审批'
            else:
                plain_content = f'{base_content}：工单 {order_no}（申请人：{applicant_name}）'
        elif category_name:
            # 只有工单类别
            if action == 'new':
                plain_content = f'您有新的工单待审批：{order_no}（类别：{category_name}）'
            elif action == 'transferred':
                plain_content = f'工单 {order_no}（类别：{category_name}）已转派给您审批'
            else:
                plain_content = f'{base_content}：工单 {order_no}（类别：{category_name}）'
        else:
            # 都没有，使用基础内容
            plain_content = f'{base_content}：{order_no}'
        
        # 构建HTML格式的邮件内容（带样式和链接）
        # 问候语
        greeting = "老师：您好！"
        
        # 邮件正文内容
        if applicant_name and category_name:
            if action == 'new':
                email_body = f'{applicant_name} 提交的工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>）需要您审批。'
            elif action == 'transferred':
                email_body = f'工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>，申请人：<strong>{applicant_name}</strong>）已转派给您审批。'
            else:
                email_body = f'{base_content}：工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>，申请人：<strong>{applicant_name}</strong>）。'
        elif applicant_name:
            if action == 'new':
                email_body = f'{applicant_name} 提交的工单 <strong>{order_no}</strong> 需要您审批。'
            elif action == 'transferred':
                email_body = f'工单 <strong>{order_no}</strong>（申请人：<strong>{applicant_name}</strong>）已转派给您审批。'
            else:
                email_body = f'{base_content}：工单 <strong>{order_no}</strong>（申请人：<strong>{applicant_name}</strong>）。'
        elif category_name:
            if action == 'new':
                email_body = f'您有新的工单待审批：<strong>{order_no}</strong>（类别：<strong>{category_name}</strong>）。'
            elif action == 'transferred':
                email_body = f'工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>）已转派给您审批。'
            else:
                email_body = f'{base_content}：工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>）。'
        else:
            email_body = f'{base_content}：<strong>{order_no}</strong>。'
        
        # 结尾链接
        system_link = f'<a href="{frontend_url}" style="color: #409EFF; text-decoration: none;">审批系统</a>'
        ending = f'请登录{system_link}查看。'
        
        # 完整的HTML邮件内容
        html_content = f'''
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333;">
            <p style="margin: 0 0 15px 0;">{greeting}</p>
            <p style="margin: 0 0 15px 0;">{email_body}</p>
            <p style="margin: 15px 0 0 0; color: #666;">{ending}</p>
        </div>
        '''
        
        # 纯文本内容用于app通知
        notification_content = plain_content
        
        # 构建App对象（用于交我办通知）
        app_data = {
            'displayStyle': 'operation',
            'abstract': title,
            'content': [
                {'name': '工单编号', 'value': order_no}
            ]
        }
        
        if applicant_name:
            app_data['content'].append({'name': '申请人', 'value': applicant_name})
        if category_name:
            app_data['content'].append({'name': '工单类别', 'value': category_name})
        
        # 不再添加"操作"项
        
        if order_url:
            app_data['urls'] = [{
                'url': order_url,
                'urlName': '查看详情',
                'urlType': 'web'
            }]
        
        # 从email中提取jAccount账号（@字符之前的部分）
        jaccount_account = extract_jaccount_from_email(email) if email else None
        
        # 构建通知数据，同时发送 app 和 email
        channels = []
        notification_data = {
            'name': title,
            'content': notification_content,  # 纯文本内容，用于app通知
            'abstract': title,
            'app': app_data
        }
        
        # 如果有email渠道，添加HTML格式的邮件内容
        if email:
            notification_data['html'] = html_content
        
        # 添加渠道和收件人
        # 交我办通知需要jAccount账号（从email提取）
        if jaccount_account:
            notification_data['accounts'] = [jaccount_account]
            channels.append('app')
        
        # 短信通知需要手机号（如果只有手机号没有账号，使用sms渠道）
        if phone and not jaccount_account:
            notification_data['phones'] = [phone]
            channels.append('sms')
        
        # 邮件通知需要email
        if email:
            notification_data['emails'] = [email]
            channels.append('email')
        
        if not channels:
            logger.warning(f"工单通知 {order_no} 没有有效的收件人信息（需要email或phone）")
            return {
                'success': False,
                'message': '没有有效的收件人信息（需要email或phone）'
            }
        
        notification_data['channels'] = channels
        
        # 发送通知
        return self.send_notification(notification_data)


def get_notification_service():
    """获取通知服务实例"""
    return NotificationService(current_app.config)


@notification_bp.route('/notification/token', methods=['GET'])
def get_access_token():
    """获取通知接口access_token（使用密码凭据方式，仅开发环境）"""
    if not current_app.config['DEBUG']:
        return jsonify({
            'success': False,
            'message': '仅开发环境可用'
        }), 403
    
    try:
        from auth.token_client import TokenClient
        token_client = TokenClient(current_app.config)
        result = token_client.get_token(scope='send_notification')
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '成功获取access_token',
                'access_token': result['access_token'],
                'refresh_token': result.get('refresh_token'),
                'token_type': result.get('token_type', 'Bearer'),
                'expires_in': result.get('expires_in', 3600)
            })
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"获取access_token失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取access_token失败: {str(e)}'
        }), 500


@notification_bp.route('/notification/refresh', methods=['POST'])
def refresh_access_token():
    """刷新通知接口access_token（仅开发环境）"""
    if not current_app.config['DEBUG']:
        return jsonify({
            'success': False,
            'message': '仅开发环境可用'
        }), 403
    
    try:
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'success': False,
                'message': 'refresh_token参数不能为空'
            }), 400
        
        from auth.token_client import TokenClient
        token_client = TokenClient(current_app.config)
        result = token_client.refresh_token(refresh_token)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '成功刷新access_token',
                'access_token': result['access_token'],
                'refresh_token': result.get('refresh_token'),
                'token_type': result.get('token_type', 'Bearer'),
                'expires_in': result.get('expires_in', 3600)
            })
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"刷新access_token失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'刷新access_token失败: {str(e)}'
        }), 500


@notification_bp.route('/notification/test', methods=['POST'])
def test_notification():
    """测试通知接口（仅开发环境）"""
    if not current_app.config['DEBUG']:
        return jsonify({
            'success': False,
            'message': '仅开发环境可用'
        }), 403
    
    data = request.get_json()
    service = get_notification_service()
    
    # 支持多种测试方式
    if 'notification_data' in data:
        # 直接发送通知数据
        result = service.send_notification(data['notification_data'])
    elif 'account' in data:
        # 发送给账号
        result = service.send_to_account(
            data['account'],
            data.get('title', '测试通知'),
            data.get('content', '这是一条测试通知'),
            data.get('channels', ['app'])
        )
    else:
        result = {
            'success': False,
            'message': '请提供notification_data或account参数'
        }
    
    return jsonify(result)

