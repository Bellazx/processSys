"""
表单配置相关数据模型
"""

from . import db
from datetime import datetime
import json


class FormConfig(db.Model):
    """表单配置表"""
    __tablename__ = 'process_sys_form_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, nullable=False, comment='工单类别ID')
    name = db.Column(db.String(100), nullable=False, comment='表单名称')
    version = db.Column(db.Integer, default=1, comment='版本号')
    
    # 表单状态：draft草稿/published已发布/archived已归档
    status = db.Column(db.String(20), default='draft', comment='状态')
    
    # 表单字段配置（JSON格式存储）
    fields_config = db.Column(db.Text, comment='字段配置JSON')
    
    # 系统字段排序配置（JSON格式存储，用于存储系统自动字段的排序顺序）
    # 注意：如果数据库表还没有这个字段，需要先运行迁移脚本添加
    # 临时注释：如果数据库表还没有这个字段，请先运行 add_system_fields_order_column.py 添加字段
    # system_fields_order = db.Column(db.Text, nullable=True, comment='系统字段排序配置JSON')
    
    # 临时解决方案：使用 @property 动态访问字段，避免 SQLAlchemy 查询时报错
    @property
    def _system_fields_order(self):
        """临时属性，用于检查字段是否存在"""
        try:
            return getattr(self, 'system_fields_order', None)
        except:
            return None
    
    # 操作人信息
    creator_id = db.Column(db.String(50), comment='创建人学工号')
    creator_name = db.Column(db.String(100), comment='创建人姓名')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    publish_time = db.Column(db.DateTime, comment='发布时间')
    
    # 关联关系
    fields = db.relationship('FormField', backref='form_config', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_fields_config(self):
        """获取字段配置（解析JSON）"""
        if self.fields_config:
            try:
                return json.loads(self.fields_config)
            except:
                return []
        return []
    
    def set_fields_config(self, config):
        """设置字段配置（转换为JSON）"""
        self.fields_config = json.dumps(config, ensure_ascii=False)
    
    def get_system_fields_order(self):
        """获取系统字段排序配置（解析JSON）"""
        # 兼容旧数据：如果字段不存在，返回空字典
        try:
            # 尝试访问字段，如果不存在会抛出 AttributeError
            field_value = getattr(self, 'system_fields_order', None)
            if field_value is None:
                return {}
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, TypeError):
                return {}
        except AttributeError:
            # 字段不存在，返回空字典
            return {}
    
    def set_system_fields_order(self, order_config):
        """设置系统字段排序配置（转换为JSON）"""
        # 兼容旧数据：如果字段不存在，跳过设置
        try:
            # 检查字段是否在模型中定义
            if hasattr(self.__class__, 'system_fields_order'):
                self.system_fields_order = json.dumps(order_config, ensure_ascii=False)
        except (AttributeError, KeyError):
            # 字段不存在，忽略设置
            pass
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'version': self.version,
            'status': self.status,
            'fields_config': self.get_fields_config(),
            'creator_id': self.creator_id,
            'creator_name': self.creator_name,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'publish_time': self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None
        }
        # 兼容处理：如果字段存在，添加 system_fields_order
        try:
            result['system_fields_order'] = self.get_system_fields_order()
        except:
            result['system_fields_order'] = {}
        return result


class FormField(db.Model):
    """表单字段表（可选，用于更细粒度的字段管理）"""
    __tablename__ = 'process_sys_form_field'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    form_config_id = db.Column(db.Integer, db.ForeignKey('process_sys_form_config.id'), nullable=False, comment='表单配置ID')
    
    field_key = db.Column(db.String(50), nullable=False, comment='字段标识')
    field_label = db.Column(db.String(100), nullable=False, comment='字段标签')
    field_type = db.Column(db.String(20), nullable=False, comment='字段类型：text/number/textarea/image/file/select等')
    field_options = db.Column(db.Text, comment='字段选项（JSON格式，用于select等类型）')
    is_required = db.Column(db.Boolean, default=False, comment='是否必填')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'form_config_id': self.form_config_id,
            'field_key': self.field_key,
            'field_label': self.field_label,
            'field_type': self.field_type,
            'field_options': self.field_options,
            'is_required': self.is_required,
            'sort_order': self.sort_order
        }

