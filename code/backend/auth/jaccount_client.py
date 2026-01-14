"""
jAccount OAuth2/OIDC客户端
"""

import requests
import jwt
import logging
from urllib.parse import urlencode, parse_qs, urlparse
import secrets
import hashlib
import base64

logger = logging.getLogger(__name__)


class JAccountClient:
    """jAccount OAuth2/OIDC客户端"""
    
    def __init__(self, config):
        # config可能是Flask的config字典或配置对象
        if isinstance(config, dict):
            self.client_id = config.get('JACCOUNT_CLIENT_ID')
            self.client_secret = config.get('JACCOUNT_CLIENT_SECRET')
            self.authorization_url = config.get('JACCOUNT_AUTHORIZATION_URL')
            self.token_url = config.get('JACCOUNT_TOKEN_URL')
            self.userinfo_url = config.get('JACCOUNT_USERINFO_URL')
            self.logout_url = config.get('JACCOUNT_LOGOUT_URL')
            self.redirect_uri = config.get('JACCOUNT_REDIRECT_URI')
        else:
            # 如果是配置对象
            self.client_id = getattr(config, 'JACCOUNT_CLIENT_ID', None)
            self.client_secret = getattr(config, 'JACCOUNT_CLIENT_SECRET', None)
            self.authorization_url = getattr(config, 'JACCOUNT_AUTHORIZATION_URL', None)
            self.token_url = getattr(config, 'JACCOUNT_TOKEN_URL', None)
            self.userinfo_url = getattr(config, 'JACCOUNT_USERINFO_URL', None)
            self.logout_url = getattr(config, 'JACCOUNT_LOGOUT_URL', None)
            self.redirect_uri = getattr(config, 'JACCOUNT_REDIRECT_URI', None)
    
    def get_authorization_url(self, state=None):
        """
        获取授权URL
        
        Args:
            state: 状态参数，用于防止CSRF攻击
            
        Returns:
            str: 授权URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'response_type': 'code',
            'scope': 'profile',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state
        }
        
        url = f"{self.authorization_url}?{urlencode(params)}"
        logger.info(f"生成授权URL: {url}")
        return url, state
    
    def get_token(self, code):
        """
        使用授权码获取访问令牌和ID令牌
        
        Args:
            code: 授权码
            
        Returns:
            dict: 包含access_token, refresh_token, id_token等
        """
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
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
            logger.info("成功获取token")
            return {
                'success': True,
                'data': token_data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"获取token失败: {e}")
            return {
                'success': False,
                'message': f'获取token失败: {str(e)}'
            }
    
    def verify_id_token(self, id_token):
        """
        验证并解析ID令牌
        
        Args:
            id_token: JWT格式的ID令牌
            
        Returns:
            dict: 解析后的用户信息
        """
        try:
            # 注意：实际验证需要使用jAccount的公钥，这里先简单解析
            # 生产环境需要验证签名
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False}  # 开发环境跳过签名验证
            )
            
            user_info = {
                'sub': decoded.get('sub'),  # jAccount账号
                'name': decoded.get('name'),  # 姓名
                'code': decoded.get('code'),  # 学工号
                'type': decoded.get('type'),  # 身份类型
            }
            
            logger.info(f"解析ID令牌成功: {user_info}")
            return {
                'success': True,
                'data': user_info
            }
        except Exception as e:
            logger.error(f"解析ID令牌失败: {e}")
            return {
                'success': False,
                'message': f'解析ID令牌失败: {str(e)}'
            }
    
    def get_user_profile(self, access_token):
        """
        使用访问令牌获取用户详细信息（Profile API）
        
        Args:
            access_token: 访问令牌
            
        Returns:
            dict: 用户详细信息
        """
        try:
            # Profile API支持两种方式：query参数或Authorization头
            # 根据文档，使用query参数方式
            url = f"{self.userinfo_url}?access_token={access_token}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Profile API响应: {result}")
            
            # Profile API返回格式：{'errno': 0, 'error': 'success', 'entities': [...]}
            if result.get('errno') == 0 and result.get('entities'):
                # 取第一个实体作为用户信息
                profile = result['entities'][0]
                logger.info(f"成功获取用户信息: {profile}")
                return {
                    'success': True,
                    'data': profile
                }
            else:
                error_msg = result.get('error', '未知错误')
                logger.error(f"Profile API返回错误: {error_msg}")
                return {
                    'success': False,
                    'message': f'获取用户信息失败: {error_msg}'
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"获取用户信息失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应状态码: {e.response.status_code}")
                try:
                    logger.error(f"响应内容: {e.response.text}")
                except:
                    pass
            return {
                'success': False,
                'message': f'获取用户信息失败: {str(e)}'
            }
    
    def get_logout_url(self, post_logout_redirect_uri=None, state=None):
        """
        获取登出URL
        
        根据jAccount文档：
        GET http://jaccount.sjtu.edu.cn/oauth2/logout
        参数：
        - client_id（必填）：jAccount 成员站点的身份标识
        - post_logout_redirect_uri（必填）：回调地址
        - state（可选）：提供时通过回调地址回传
        
        Args:
            post_logout_redirect_uri: 登出后重定向地址，默认为前端首页
            state: 状态参数，用于防止CSRF攻击
            
        Returns:
            str: 登出URL
        """
        if not post_logout_redirect_uri:
            # 默认重定向到后端登出回调接口，由后端处理后再重定向到前端登录页
            # 这样可以确保URL格式正确，并处理state参数
            # 从redirect_uri提取前端基础URL
            # 从redirect_uri提取前端基础URL，如果没有则从配置获取
            if '/process' in self.redirect_uri:
                redirect_base = self.redirect_uri.rsplit('/process', 1)[0]
            else:
                # 尝试从配置获取FRONTEND_URL
                if isinstance(self.config, dict):
                    redirect_base = self.config.get('FRONTEND_URL', 'http://202.121.183.240:3003')
                else:
                    redirect_base = getattr(self.config, 'FRONTEND_URL', 'http://202.121.183.240:3003')
            # 添加一个占位查询参数，确保jAccount使用&追加参数时格式正确
            # 如果URL已经有?参数，jAccount会使用&追加；如果没有，jAccount可能会使用&而不是?
            post_logout_redirect_uri = f"{redirect_base}/process/auth/logout/callback?callback=1"
        
        params = {
            'client_id': self.client_id,
            'post_logout_redirect_uri': post_logout_redirect_uri
        }
        
        if state:
            params['state'] = state
        
        url = f"{self.logout_url}?{urlencode(params)}"
        logger.info(f"生成登出URL: {url}")
        return url

