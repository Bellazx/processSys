"""
获取通知接口access_token的客户端
使用资源拥有者密码凭据许可(Resource Owner Password Credentials Grant)方式
"""

import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class TokenClient:
    """Token获取客户端"""
    
    def __init__(self, config):
        # 保存config引用，以便后续使用
        self.config = config
        
        # config可能是Flask的config字典或配置对象
        if isinstance(config, dict):
            self.client_id = config.get('NOTIFICATION_CLIENT_ID')
            self.client_secret = config.get('NOTIFICATION_CLIENT_SECRET')
            account = config.get('NOTIFICATION_ACCOUNT', '')
            self.password = config.get('NOTIFICATION_PASSWORD')
        else:
            self.client_id = getattr(config, 'NOTIFICATION_CLIENT_ID', None)
            self.client_secret = getattr(config, 'NOTIFICATION_CLIENT_SECRET', None)
            account = getattr(config, 'NOTIFICATION_ACCOUNT', '')
            self.password = getattr(config, 'NOTIFICATION_PASSWORD', None)
        
        # 从邮箱中提取jAccount账号（@之前的部分）
        # 如果已经是jAccount账号（不包含@），则直接使用
        if account and '@' in account:
            self.username = account.split('@')[0]
            logger.info(f"从邮箱 {account} 提取jAccount账号: {self.username}")
        else:
            self.username = account
        
        # 通知接口获取token使用jAccount的token endpoint
        self.token_url = 'https://jaccount.sjtu.edu.cn/oauth2/token'
    
    def get_token(self, scope='send_notification'):
        """
        使用资源拥有者密码凭据许可方式获取access_token
        
        Args:
            scope: 授权范围，通知接口需要send_notification
            
        Returns:
            dict: 包含access_token和refresh_token的结果
        """
        if not self.client_id or not self.client_secret:
            return {
                'success': False,
                'message': '通知接口客户端凭据未配置'
            }
        
        # 使用初始化时已经提取的username和password
        # 这些值在__init__中已经从config中提取并处理过了
        username = self.username
        password = self.password
        
        data = {
            'grant_type': 'password',
            'scope': scope,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': username,
            'password': password
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            # 记录请求信息（不记录密码）
            logger.info(f"请求token: grant_type=password, scope={scope}, client_id={self.client_id}, username={username}")
            
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            
            # 如果响应不是200，记录详细错误信息
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = f" 错误详情: {error_json}"
                except:
                    error_detail = f" 响应内容: {response.text[:200]}"
                
                logger.error(f"获取token失败: HTTP {response.status_code}{error_detail}")
                return {
                    'success': False,
                    'message': f'获取token失败: HTTP {response.status_code}{error_detail}',
                    'status_code': response.status_code,
                    'error_detail': error_detail
                }
            
            response.raise_for_status()
            token_data = response.json()
            logger.info("成功获取通知接口access_token")
            return {
                'success': True,
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': token_data.get('expires_in', 3600),
                'data': token_data
            }
        except requests.exceptions.RequestException as e:
            # 如果是HTTPError，尝试获取响应内容
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f" 错误详情: {error_json}"
                except:
                    error_detail = f" 响应内容: {e.response.text[:200]}"
            
            logger.error(f"获取token失败: {e}{error_detail}")
            return {
                'success': False,
                'message': f'获取token失败: {str(e)}{error_detail}',
                'error_detail': error_detail
            }
    
    def refresh_token(self, refresh_token):
        """
        使用refresh_token刷新access_token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            dict: 包含新的access_token和refresh_token的结果
        """
        if not refresh_token:
            return {
                'success': False,
                'message': 'refresh_token不能为空'
            }
        
        if not self.client_id or not self.client_secret:
            return {
                'success': False,
                'message': '通知接口客户端凭据未配置'
            }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            token_data = response.json()
            logger.info("成功刷新通知接口access_token")
            return {
                'success': True,
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': token_data.get('expires_in', 3600),
                'data': token_data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"刷新token失败: {e}")
            return {
                'success': False,
                'message': f'刷新token失败: {str(e)}'
            }


def get_token_client():
    """获取Token客户端实例"""
    return TokenClient(current_app.config)

