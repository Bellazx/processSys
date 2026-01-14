"""
管理员配置路由
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
import logging
from sqlalchemy import text
from models import db, AdminConfig, DepartmentAdmin, CategoryConfig, CategoryAdmin, Staff
from auth.decorators import login_required, permission_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def get_staff_by_cardno(cardno):
    """
    根据学工号（cardno）查询员工信息
    使用原生SQL查询，因为实际列名是cardno不是code
    """
    try:
        sql = "SELECT id, name, cardno, depart, mobilephone, email, gender, status FROM staff WHERE cardno = :cardno AND status = '在职'"
        result = db.session.execute(text(sql), {'cardno': cardno})
        row = result.fetchone()
        
        if not row:
            return None
        
        # 构造staff对象（用于兼容现有代码）
        class StaffObj:
            def __init__(self, row_data):
                self.id = row_data[0]
                self.name = row_data[1]
                self.cardno = row_data[2]
                self.code = row_data[2]  # 兼容code属性
                self.depart = row_data[3]
                self.dept = row_data[3]  # 兼容dept属性
                self.mobilephone = row_data[4] if len(row_data) > 4 and row_data[4] else None
                self.phone = self.mobilephone  # 保持向后兼容
                self.email = row_data[5] if len(row_data) > 5 and row_data[5] else None
                self.gender = row_data[6] if len(row_data) > 6 and row_data[6] else None
                self.status = row_data[7] if len(row_data) > 7 and row_data[7] else None
        
        return StaffObj(row)
    except Exception as e:
        logger.error(f"查询员工信息失败: {e}", exc_info=True)
        return None


# ============= 系统管理员配置 =============

@admin_bp.route('/admin-configs', methods=['GET'])
@login_required
@permission_required('super_admin')
def get_admin_configs():
    """获取系统管理员列表"""
    try:
        admins = AdminConfig.query.order_by(AdminConfig.create_time.desc()).all()
        return jsonify({
            'success': True,
            'data': [admin.to_dict() for admin in admins]
        })
    except Exception as e:
        logger.error(f"获取管理员列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取管理员列表失败'
        }), 500


@admin_bp.route('/admin-configs', methods=['POST'])
@login_required
@permission_required('super_admin')
def create_admin_config():
    """创建系统管理员"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        # 检查是否已存在
        existing = AdminConfig.query.filter_by(user_id=user_id).first()
        if existing:
            return jsonify({
                'success': False,
                'message': '该用户已是管理员'
            }), 400
        
        # 从staff表获取用户信息（使用cardno列）
        staff = get_staff_by_cardno(user_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': '用户不存在或不在职'
            }), 400
        
        admin = AdminConfig(
            user_id=user_id,
            user_name=staff.name,
            can_manage_form=data.get('can_manage_form', False),
            can_manage_external=data.get('can_manage_external', False),
            is_super_admin=data.get('is_super_admin', False)
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '管理员创建成功',
            'data': {'id': admin.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '创建管理员失败'
        }), 500


@admin_bp.route('/admin-configs/<int:admin_id>', methods=['PUT'])
@login_required
@permission_required('super_admin')
def update_admin_config(admin_id):
    """更新系统管理员"""
    try:
        data = request.get_json()
        admin = AdminConfig.query.get(admin_id)
        
        if not admin:
            return jsonify({
                'success': False,
                'message': '管理员不存在'
            }), 404
        
        if 'can_manage_form' in data:
            admin.can_manage_form = data['can_manage_form']
        if 'can_manage_external' in data:
            admin.can_manage_external = data['can_manage_external']
        if 'is_super_admin' in data:
            admin.is_super_admin = data['is_super_admin']
        
        admin.update_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '管理员更新成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '更新管理员失败'
        }), 500


@admin_bp.route('/admin-configs/<int:admin_id>', methods=['DELETE'])
@login_required
@permission_required('super_admin')
def delete_admin_config(admin_id):
    """删除系统管理员"""
    try:
        admin = AdminConfig.query.get(admin_id)
        
        if not admin:
            return jsonify({
                'success': False,
                'message': '管理员不存在'
            }), 404
        
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '管理员删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '删除管理员失败'
        }), 500


# ============= 部门管理员配置 =============

@admin_bp.route('/department-admins', methods=['GET'])
@login_required
@permission_required('super_admin')
def get_department_admins():
    """获取部门管理员列表"""
    try:
        admins = DepartmentAdmin.query.order_by(DepartmentAdmin.dept_name).all()
        return jsonify({
            'success': True,
            'data': [admin.to_dict() for admin in admins]
        })
    except Exception as e:
        logger.error(f"获取部门管理员列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取部门管理员列表失败'
        }), 500


@admin_bp.route('/departments', methods=['GET'])
@login_required
def get_departments():
    """获取部门列表（从部门管理员表中查询distinct dept_name）"""
    try:
        # 使用distinct查询去重的部门名称
        departments = db.session.query(DepartmentAdmin.dept_name).distinct().order_by(DepartmentAdmin.dept_name).all()
        dept_list = [dept[0] for dept in departments if dept[0]]
        
        return jsonify({
            'success': True,
            'data': dept_list
        })
    except Exception as e:
        logger.error(f"获取部门列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取部门列表失败'
        }), 500


@admin_bp.route('/department-admins', methods=['POST'])
@login_required
@permission_required('super_admin')
def create_department_admin():
    """创建部门管理员"""
    try:
        data = request.get_json()
        dept_name = data.get('dept_name')
        admin_id = data.get('admin_id')
        
        # 检查是否已存在
        existing = DepartmentAdmin.query.filter_by(
            dept_name=dept_name,
            admin_id=admin_id
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'message': '该部门管理员已存在'
            }), 400
        
        # 从staff表获取用户信息（使用cardno列）
        staff = get_staff_by_cardno(admin_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': '用户不存在或不在职'
            }), 400
        
        admin = DepartmentAdmin(
            dept_name=dept_name,
            admin_id=admin_id,
            admin_name=staff.name
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '部门管理员创建成功',
            'data': {'id': admin.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建部门管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '创建部门管理员失败'
        }), 500


@admin_bp.route('/department-admins/<int:admin_id>', methods=['DELETE'])
@login_required
@permission_required('super_admin')
def delete_department_admin(admin_id):
    """删除部门管理员"""
    try:
        admin = DepartmentAdmin.query.get(admin_id)
        
        if not admin:
            return jsonify({
                'success': False,
                'message': '部门管理员不存在'
            }), 404
        
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '部门管理员删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除部门管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '删除部门管理员失败'
        }), 500


# ============= 工单类别配置 =============

@admin_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """获取工单类别列表"""
    try:
        is_active = request.args.get('is_active')
        query = CategoryConfig.query
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active == 'true')
        
        categories = query.order_by(CategoryConfig.sort_order, CategoryConfig.id).all()
        return jsonify({
            'success': True,
            'data': [cat.to_dict() for cat in categories]
        })
    except Exception as e:
        logger.error(f"获取工单类别列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取工单类别列表失败'
        }), 500


def generate_category_code(category_name):
    """
    根据类别名称自动生成类别代码
    规则：
    1. 如果是英文，取前5个大写字母
    2. 如果是中文，使用拼音首字母（如果安装了pypinyin）或使用序号
    3. 如果重复，自动添加序号
    """
    import re
    import time
    
    # 清理类别名称
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', category_name.strip())
    if not name:
        base_code = 'CAT'
    else:
        # 如果是纯英文，取前5个大写字母
        if re.match(r'^[a-zA-Z]+$', name):
            base_code = name[:5].upper()
        else:
            # 尝试使用pypinyin库（如果已安装）
            try:
                from pypinyin import lazy_pinyin, Style
                # 获取拼音首字母
                initials = ''.join([p[0].upper() for p in lazy_pinyin(name, style=Style.FIRST_LETTER)])
                base_code = initials[:5] if initials else 'CAT'
            except ImportError:
                # 如果没有pypinyin库，使用序号方案
                # 获取现有类别的数量，生成序号
                count = CategoryConfig.query.count()
                next_num = count + 1
                base_code = f'CAT{next_num:03d}'
    
    # 如果base_code已经是带序号的格式，直接使用
    if re.match(r'^[A-Z]+\d+$', base_code):
        category_code = base_code
    else:
        # 检查是否已存在，如果存在则添加序号
        counter = 1
        category_code = base_code
        while CategoryConfig.query.filter_by(category_code=category_code).first():
            category_code = f"{base_code}{counter:03d}"
            counter += 1
            # 防止无限循环
            if counter > 999:
                # 如果序号超过999，使用时间戳后4位
                category_code = f"{base_code}{int(time.time()) % 10000:04d}"
                break
    
    return category_code


@admin_bp.route('/categories', methods=['POST'])
@login_required
@permission_required('super_admin')
def create_category():
    """创建工单类别（类别代码自动生成）"""
    try:
        data = request.get_json()
        category_name = data.get('category_name')
        
        if not category_name:
            return jsonify({
                'success': False,
                'message': '类别名称不能为空'
            }), 400
        
        # 自动生成类别代码
        category_code = generate_category_code(category_name)
        
        category = CategoryConfig(
            category_code=category_code,
            category_name=category_name,
            description=data.get('description', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单类别创建成功',
            'data': {
                'id': category.id,
                'category_code': category_code
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建工单类别失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'创建工单类别失败: {str(e)}'
        }), 500


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
@permission_required('super_admin')
def update_category(category_id):
    """更新工单类别"""
    try:
        data = request.get_json()
        category = CategoryConfig.query.get(category_id)
        
        if not category:
            return jsonify({
                'success': False,
                'message': '工单类别不存在'
            }), 404
        
        if 'category_name' in data:
            category.category_name = data['category_name']
        if 'description' in data:
            category.description = data['description']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        if 'is_active' in data:
            category.is_active = data['is_active']
        
        category.update_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单类别更新成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新工单类别失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '更新工单类别失败'
        }), 500


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
@permission_required('super_admin')
def delete_category(category_id):
    """删除工单类别"""
    try:
        category = CategoryConfig.query.get(category_id)
        
        if not category:
            return jsonify({
                'success': False,
                'message': '工单类别不存在'
            }), 404
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单类别删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除工单类别失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '删除工单类别失败'
        }), 500


# ============= 工单类别管理员配置 =============

@admin_bp.route('/category-admins', methods=['GET'])
@login_required
@permission_required('super_admin')
def get_category_admins():
    """获取工单类别管理员列表"""
    try:
        category_id = request.args.get('category_id')
        query = CategoryAdmin.query
        
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        
        admins = query.all()
        return jsonify({
            'success': True,
            'data': [admin.to_dict() for admin in admins]
        })
    except Exception as e:
        logger.error(f"获取类别管理员列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取类别管理员列表失败'
        }), 500


@admin_bp.route('/category-admins', methods=['POST'])
@login_required
@permission_required('super_admin')
def create_category_admin():
    """创建工单类别管理员"""
    try:
        data = request.get_json()
        category_id = data.get('category_id')
        admin_id = data.get('admin_id')
        
        # 检查是否已存在
        existing = CategoryAdmin.query.filter_by(
            category_id=category_id,
            admin_id=admin_id
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'message': '该类别管理员已存在'
            }), 400
        
        # 从staff表获取用户信息（使用cardno列）
        staff = get_staff_by_cardno(admin_id)
        if not staff:
            return jsonify({
                'success': False,
                'message': '用户不存在或不在职'
            }), 400
        
        admin = CategoryAdmin(
            category_id=category_id,
            admin_id=admin_id,
            admin_name=staff.name
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '类别管理员创建成功',
            'data': {'id': admin.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建类别管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '创建类别管理员失败'
        }), 500


@admin_bp.route('/category-admins/<int:admin_id>', methods=['DELETE'])
@login_required
@permission_required('super_admin')
def delete_category_admin(admin_id):
    """删除工单类别管理员"""
    try:
        admin = CategoryAdmin.query.get(admin_id)
        
        if not admin:
            return jsonify({
                'success': False,
                'message': '类别管理员不存在'
            }), 404
        
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '类别管理员删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除类别管理员失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '删除类别管理员失败'
        }), 500


# ============= 员工搜索 =============

@admin_bp.route('/staff/table-info', methods=['GET'])
@login_required
def get_staff_table_info():
    """获取staff表的列信息（用于调试）"""
    try:
        from sqlalchemy import text
        
        # 查询表结构
        table_info_sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'staff'
        ORDER BY ORDINAL_POSITION
        """
        
        result = db.session.execute(text(table_info_sql))
        columns = []
        for row in result:
            columns.append({
                'column_name': row[0],
                'data_type': row[1],
                'is_nullable': row[2]
            })
        
        return jsonify({
            'success': True,
            'data': columns
        })
    except Exception as e:
        logger.error(f"获取表结构失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取表结构失败: {str(e)}'
        }), 500


@admin_bp.route('/staff/search', methods=['GET'])
@login_required
def search_staff():
    """
    搜索员工（用于选择审批人等）
    只返回status为"在职"的人员
    支持按学工号、姓名搜索
    
    使用原生SQL查询，自动识别表结构
    """
    try:
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 20))
        
        from sqlalchemy import text
        
        # 先查询表结构，识别实际列名
        table_info_sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'staff'
        ORDER BY ORDINAL_POSITION
        """
        
        result = db.session.execute(text(table_info_sql))
        all_columns = [row[0] for row in result]
        logger.info(f"staff表所有列名: {all_columns}")
        
        # 识别关键列名
        code_column = None  # 学工号列
        name_column = None  # 姓名列
        dept_column = None  # 部门列
        status_column = None  # 状态列
        id_column = None  # ID列
        phone_column = None  # 手机号列
        email_column = None  # 邮箱列
        gender_column = None  # 性别列
        
        for col_name in all_columns:
            col_lower = col_name.lower()
            # 识别ID列
            if col_lower == 'id':
                id_column = col_name
            # 识别学工号列（优先cardno，然后是code、工号、学工号、employee_id等）
            elif not code_column:
                if col_lower == 'cardno' or 'cardno' in col_lower:
                    code_column = col_name
                elif 'code' in col_lower or '工号' in col_name or '学工号' in col_name or 'employee_id' in col_lower or 'staff_code' in col_lower:
                    code_column = col_name
            # 识别姓名列
            elif not name_column and ('name' in col_lower or '姓名' in col_name or 'staff_name' in col_lower):
                name_column = col_name
            # 识别部门列（优先depart，然后是dept、部门、department等）
            elif not dept_column:
                if col_lower == 'depart' or 'depart' in col_lower:
                    dept_column = col_name
                elif 'dept' in col_lower or '部门' in col_name or 'department' in col_lower:
                    dept_column = col_name
            # 识别状态列
            elif not status_column and ('status' in col_lower or '状态' in col_name or '员工状态' in col_name):
                status_column = col_name
            # 识别手机号列（优先phone，然后是mobilephone、手机、电话等）
            elif not phone_column:
                if col_lower == 'phone' or col_lower == 'mobilephone':
                    phone_column = col_name
                elif 'phone' in col_lower or '手机' in col_name or 'mobile' in col_lower or '电话' in col_name:
                    phone_column = col_name
            # 识别邮箱列
            elif not email_column and ('email' in col_lower or '邮箱' in col_name or 'mail' in col_lower):
                email_column = col_name
            # 识别性别列
            elif not gender_column and ('gender' in col_lower or '性别' in col_name or 'sex' in col_lower):
                gender_column = col_name
        
        # 检查必需列
        if not id_column:
            id_column = all_columns[0] if all_columns else 'id'  # 默认使用第一列作为ID
        
        if not code_column:
            return jsonify({
                'success': False,
                'message': f'无法识别学工号列。实际列名: {all_columns}'
            }), 500
        
        if not name_column:
            return jsonify({
                'success': False,
                'message': f'无法识别姓名列。实际列名: {all_columns}'
            }), 500
        
        if not status_column:
            return jsonify({
                'success': False,
                'message': f'无法识别状态列。实际列名: {all_columns}'
            }), 500
        
        # 构建SELECT子句
        select_fields = [id_column, name_column, code_column]
        field_aliases = ['id', 'name', 'code']
        
        if dept_column:
            select_fields.append(dept_column)
            field_aliases.append('dept')
        else:
            select_fields.append('NULL')
            field_aliases.append('dept')
        
        if phone_column:
            select_fields.append(phone_column)
            field_aliases.append('phone')
        else:
            select_fields.append('NULL')
            field_aliases.append('phone')
        
        if email_column:
            select_fields.append(email_column)
            field_aliases.append('email')
        else:
            select_fields.append('NULL')
            field_aliases.append('email')
        
        if gender_column:
            select_fields.append(gender_column)
            field_aliases.append('gender')
        else:
            select_fields.append('NULL')
            field_aliases.append('gender')
        
        select_fields.append(status_column)
        field_aliases.append('status')
        
        # 构建SQL查询
        select_clause = ', '.join([f'{field} as {alias}' for field, alias in zip(select_fields, field_aliases)])
        
        sql = f"""
        SELECT TOP {limit} {select_clause}
        FROM staff
        WHERE {status_column} = '在职'
        """
        
        # 添加搜索条件
        if keyword:
            # 使用参数化查询防止SQL注入
            sql += f" AND ({name_column} LIKE :keyword OR {code_column} LIKE :keyword)"
        
        # 添加排序
        sql += f" ORDER BY {code_column}, {name_column}"
        
        # 执行查询
        if keyword:
            result = db.session.execute(text(sql), {'keyword': f'%{keyword}%'})
        else:
            result = db.session.execute(text(sql))
        
        rows = result.fetchall()
        
        # 转换为字典
        data = []
        for row in rows:
            row_dict = {}
            for i, alias in enumerate(field_aliases):
                if i < len(row):
                    row_dict[alias] = row[i] if row[i] is not None else None
            data.append(row_dict)
        
        logger.info(f"查询成功，返回 {len(data)} 条记录")
        
        return jsonify({
            'success': True,
            'data': data
        })
                
    except Exception as e:
        logger.error(f"搜索员工失败: {e}", exc_info=True)
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'搜索员工失败: {str(e)}'
        }), 500
