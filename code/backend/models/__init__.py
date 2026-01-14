"""
数据库模型模块
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .work_order import WorkOrder, WorkOrderFlow
from .form_config import FormConfig, FormField
from .admin_config import AdminConfig, DepartmentAdmin, CategoryConfig, CategoryAdmin
from .staff import Staff

__all__ = [
    'db',
    'WorkOrder',
    'WorkOrderFlow',
    'FormConfig',
    'FormField',
    'AdminConfig',
    'DepartmentAdmin',
    'CategoryConfig',
    'CategoryAdmin',
    'Staff'
]

