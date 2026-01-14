"""
员工信息模型（只读，从现有staff表读取）
"""

from . import db


class Staff(db.Model):
    """员工信息表（只读）"""
    __tablename__ = 'staff'
    
    # 根据实际staff表结构调整字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), comment='姓名')
    gender = db.Column(db.String(10), comment='性别')
    dept = db.Column(db.String(100), comment='部门')
    phone = db.Column(db.String(20), comment='手机号')
    email = db.Column(db.String(100), comment='邮箱')
    code = db.Column(db.String(50), comment='工号（学工号）')
    status = db.Column(db.String(20), comment='状态（在职/离职等）')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'dept': self.dept,
            'phone': self.phone,
            'email': self.email,
            'code': self.code,
            'status': self.status
        }

