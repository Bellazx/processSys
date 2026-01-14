"""
工单相关数据模型
"""

from . import db
from datetime import datetime


class WorkOrder(db.Model):
    """工单信息表"""
    __tablename__ = 'process_sys_work_order'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='工单编号')
    category_id = db.Column(db.Integer, nullable=False, comment='工单类别ID')
    form_config_id = db.Column(db.Integer, comment='表单配置ID')
    
    # 申请人信息（自动填充，不可修改）
    applicant_id = db.Column(db.String(50), nullable=False, comment='申请人学工号')
    applicant_name = db.Column(db.String(100), nullable=False, comment='申请人姓名')
    applicant_dept = db.Column(db.String(100), comment='申请人部门')
    applicant_phone = db.Column(db.String(20), comment='申请人手机号')
    applicant_email = db.Column(db.String(100), comment='申请人邮箱')
    apply_date = db.Column(db.Date, nullable=False, default=datetime.now().date, comment='申请日期')
    
    # 工单状态
    status = db.Column(db.String(20), nullable=False, default='draft', 
                      comment='状态：draft草稿/pending待处理/rejected已拒绝/completed已完成/cancelled已撤单/terminated已终止/external外派')
    
    # 分配方式：individual个人/department部门
    assign_type = db.Column(db.String(20), nullable=False, default='individual', comment='分配方式')
    assign_to_dept = db.Column(db.String(100), comment='分配给部门')
    
    # 外派信息
    is_external = db.Column(db.Boolean, default=False, comment='是否外派')
    external_name = db.Column(db.String(100), comment='外派人员姓名')
    external_phone = db.Column(db.String(20), comment='外派人员电话')
    external_result = db.Column(db.Text, comment='外派结果')
    
    # 表单数据（JSON格式存储）
    form_data = db.Column(db.Text, comment='表单数据JSON')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    complete_time = db.Column(db.DateTime, comment='完成时间')
    
    # 关联关系
    flows = db.relationship('WorkOrderFlow', backref='work_order', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'id': self.id,
            'order_no': self.order_no,
            'category_id': self.category_id,
            'form_config_id': self.form_config_id,
            'applicant_id': self.applicant_id,
            'applicant_name': self.applicant_name,
            'applicant_dept': self.applicant_dept,
            'applicant_phone': self.applicant_phone,
            'applicant_email': self.applicant_email,
            'apply_date': self.apply_date.strftime('%Y-%m-%d') if self.apply_date else None,
            'status': self.status,
            'assign_type': self.assign_type,
            'assign_to_dept': self.assign_to_dept,
            'is_external': self.is_external,
            'external_name': self.external_name,
            'external_phone': self.external_phone,
            'external_result': self.external_result,
            'form_data': self.form_data,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'complete_time': self.complete_time.strftime('%Y-%m-%d %H:%M:%S') if self.complete_time else None
        }
        
        # 尝试获取类别名称（如果有关联关系）
        try:
            if hasattr(self, 'category') and self.category:
                result['category_name'] = self.category.category_name
        except:
            pass
        
        return result


class WorkOrderFlow(db.Model):
    """工单流转记录表"""
    __tablename__ = 'process_sys_work_order_flow'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('process_sys_work_order.id'), nullable=False, comment='工单ID')
    
    # 操作信息
    action = db.Column(db.String(20), nullable=False, 
                      comment='操作类型：create创建/approve批准/reject拒绝/return打回/transfer转派/terminate终止/complete完成')
    action_user_id = db.Column(db.String(50), nullable=False, comment='操作人学工号')
    action_user_name = db.Column(db.String(100), comment='操作人姓名')
    
    # 流转信息
    from_status = db.Column(db.String(20), comment='原状态')
    to_status = db.Column(db.String(20), nullable=False, comment='新状态')
    
    # 审批人信息（如果是审批操作）
    approver_id = db.Column(db.String(50), comment='审批人学工号')
    approver_name = db.Column(db.String(100), comment='审批人姓名')
    
    # 转派信息（如果是转派操作）
    transfer_to_id = db.Column(db.String(50), comment='转派给（学工号）')
    transfer_to_name = db.Column(db.String(100), comment='转派给（姓名）')
    
    # 备注
    comment = db.Column(db.Text, comment='操作备注')
    
    # 时间戳
    create_time = db.Column(db.DateTime, default=datetime.now, comment='操作时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'action': self.action,
            'action_user_id': self.action_user_id,
            'action_user_name': self.action_user_name,
            'from_status': self.from_status,
            'to_status': self.to_status,
            'approver_id': self.approver_id,
            'approver_name': self.approver_name,
            'transfer_to_id': self.transfer_to_id,
            'transfer_to_name': self.transfer_to_name,
            'comment': self.comment,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }

