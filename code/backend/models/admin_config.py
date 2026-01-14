"""
管理员配置相关数据模型
"""

from . import db
from datetime import datetime


class AdminConfig(db.Model):
    """系统管理员配置表"""
    __tablename__ = 'process_sys_admin_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False, comment='管理员学工号')
    user_name = db.Column(db.String(100), comment='管理员姓名')
    
    # 权限配置
    can_manage_form = db.Column(db.Boolean, default=False, comment='可管理表单配置')
    can_manage_external = db.Column(db.Boolean, default=False, comment='可外派工单')
    is_super_admin = db.Column(db.Boolean, default=False, comment='是否超级管理员')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'can_manage_form': self.can_manage_form,
            'can_manage_external': self.can_manage_external,
            'is_super_admin': self.is_super_admin
        }


class DepartmentAdmin(db.Model):
    """部门管理员配置表"""
    __tablename__ = 'process_sys_department_admin'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dept_name = db.Column(db.String(100), nullable=False, comment='部门名称')
    admin_id = db.Column(db.String(50), nullable=False, comment='管理员学工号')
    admin_name = db.Column(db.String(100), comment='管理员姓名')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'dept_name': self.dept_name,
            'admin_id': self.admin_id,
            'admin_name': self.admin_name
        }


class CategoryConfig(db.Model):
    """工单类别配置表"""
    __tablename__ = 'process_sys_category_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_code = db.Column(db.String(50), unique=True, nullable=False, comment='类别代码')
    category_name = db.Column(db.String(100), nullable=False, comment='类别名称')
    description = db.Column(db.Text, comment='类别描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_code': self.category_code,
            'category_name': self.category_name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }


class CategoryAdmin(db.Model):
    """工单类别管理员配置表"""
    __tablename__ = 'process_sys_category_admin'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, nullable=False, comment='工单类别ID')
    admin_id = db.Column(db.String(50), nullable=False, comment='管理员学工号')
    admin_name = db.Column(db.String(100), comment='管理员姓名')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'admin_id': self.admin_id,
            'admin_name': self.admin_name
        }

