"""
表单配置管理路由
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
import logging
import json
from models import db, FormConfig, FormField, CategoryConfig
from auth.decorators import login_required, permission_required

logger = logging.getLogger(__name__)

form_config_bp = Blueprint('form_config', __name__)


@form_config_bp.route('/form-configs', methods=['GET'])
@login_required
def get_form_configs():
    """
    获取表单配置列表
    超级管理员和can_manage_form权限的管理员可以看到所有表单配置
    类别管理员只能看到自己管理的类别的表单配置
    """
    try:
        user_id = session.get('user_id')
        category_id = request.args.get('category_id')
        status = request.args.get('status')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        query = FormConfig.query
        
        # 如果不是超级管理员且没有can_manage_form权限，但如果是类别管理员，只能看到自己管理的类别
        if not can_manage_form and is_category_admin:
            query = query.filter(FormConfig.category_id.in_(category_ids))
        elif not can_manage_form:
            # 既不是超级管理员，也没有can_manage_form权限，也不是类别管理员，返回空列表
            return jsonify({
                'success': True,
                'data': []
            })
        
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        if status:
            query = query.filter_by(status=status)
        
        configs = query.order_by(FormConfig.create_time.desc()).all()
        
        # 为每个配置添加类别名称
        result = []
        for config in configs:
            config_dict = config.to_dict()
            # 获取类别信息
            category = CategoryConfig.query.get(config.category_id)
            if category:
                config_dict['category_name'] = category.category_name
                config_dict['category_code'] = category.category_code
            result.append(config_dict)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"获取表单配置列表失败: {e}\n{error_detail}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取表单配置列表失败: {str(e)}',
            'error_detail': error_detail if app.config.get('DEBUG') else None
        }), 500


@form_config_bp.route('/form-configs/<int:config_id>', methods=['GET'])
@login_required
def get_form_config(config_id):
    """获取表单配置详情"""
    try:
        config = FormConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '表单配置不存在'
            }), 404
        
        config_dict = config.to_dict()
        # 获取类别信息
        category = CategoryConfig.query.get(config.category_id)
        if category:
            config_dict['category_name'] = category.category_name
            config_dict['category_code'] = category.category_code
        
        return jsonify({
            'success': True,
            'data': config_dict
        })
    except Exception as e:
        logger.error(f"获取表单配置详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取表单配置详情失败'
        }), 500


@form_config_bp.route('/form-configs', methods=['POST'])
@login_required
def create_form_config():
    """
    创建表单配置
    超级管理员、can_manage_form权限的管理员、类别管理员都可以创建表单配置
    类别管理员只能为自己管理的类别创建表单配置
    """
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        category_id = data.get('category_id')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 权限检查
        if not can_manage_form and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权限创建表单配置'
            }), 403
        
        # 如果是类别管理员但不是超级管理员，检查是否有权限管理该类别
        if not is_super_admin and is_category_admin:
            if category_id not in category_ids:
                return jsonify({
                    'success': False,
                    'message': '无权限为该类别创建表单配置'
                }), 403
        
        # 获取类别信息，用于自动生成表单名称
        category = CategoryConfig.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': '工单类别不存在'
            }), 404
        
        # 检查是否已有配置（包括草稿和已发布的）
        existing = FormConfig.query.filter_by(category_id=category_id).first()
        
        if existing:
            # 如果已有配置，返回现有配置的ID，让前端直接编辑
            return jsonify({
                'success': False,
                'message': '该类别已有表单配置',
                'data': {'id': existing.id, 'existing': True}
            }), 400
        
        # 自动使用类别名称作为表单名称
        form_name = category.category_name
        
        config = FormConfig(
            category_id=category_id,
            name=form_name,  # 自动使用类别名称
            status='draft',
            creator_id=user_id,
            creator_name=user_name
        )
        
        # 设置字段配置
        fields_config = data.get('fields_config', [])
        # 过滤掉系统保留字段
        reserved_fields = [
            'applicant_name', 'applicant_id', 'applicant_code', 'applicant_dept',
            'apply_date', 'applicant_phone', 'applicant_email', 'user_type'
        ]
        filtered_fields = [
            field for field in fields_config
            if field.get('field_key', '').lower() not in reserved_fields
        ]
        config.set_fields_config(filtered_fields)
        
        # 设置系统字段排序配置
        if 'system_fields_order' in data:
            config.set_system_fields_order(data['system_fields_order'])
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '表单配置创建成功',
            'data': {'id': config.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建表单配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '创建表单配置失败'
        }), 500


@form_config_bp.route('/form-configs/<int:config_id>', methods=['PUT'])
@login_required
def update_form_config(config_id):
    """
    更新表单配置
    超级管理员、can_manage_form权限的管理员、类别管理员都可以更新表单配置
    类别管理员只能更新自己管理的类别的表单配置
    """
    try:
        data = request.get_json()
        config = FormConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': '表单配置不存在'
            }), 404
        
        user_id = session.get('user_id')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 权限检查
        if not can_manage_form and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权限更新表单配置'
            }), 403
        
        # 如果是类别管理员但不是超级管理员，检查是否有权限管理该类别
        if not is_super_admin and is_category_admin:
            if config.category_id not in category_ids:
                return jsonify({
                    'success': False,
                    'message': '无权限更新该表单配置'
                }), 403
        
        if config.status == 'published':
            return jsonify({
                'success': False,
                'message': '已发布的表单配置不能直接修改，请先下架'
            }), 400
        
        # 更新配置
        # 表单名称自动使用类别名称，不允许修改
        # 如果类别名称有变化，自动更新表单名称
        category = CategoryConfig.query.get(config.category_id)
        if category:
            config.name = category.category_name
        
        if 'fields_config' in data:
            # 过滤掉系统保留字段
            reserved_fields = [
                'applicant_name', 'applicant_id', 'applicant_code', 'applicant_dept',
                'apply_date', 'applicant_phone', 'applicant_email', 'user_type'
            ]
            filtered_fields = [
                field for field in data['fields_config']
                if field.get('field_key', '').lower() not in reserved_fields
            ]
            config.set_fields_config(filtered_fields)
        
        # 更新系统字段排序配置
        if 'system_fields_order' in data:
            config.set_system_fields_order(data['system_fields_order'])
        
        config.update_time = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '表单配置更新成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新表单配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '更新表单配置失败'
        }), 500


@form_config_bp.route('/form-configs/<int:config_id>/publish', methods=['POST'])
@login_required
def publish_form_config(config_id):
    """
    发布表单配置
    超级管理员、can_manage_form权限的管理员、类别管理员都可以发布表单配置
    类别管理员只能发布自己管理的类别的表单配置
    """
    try:
        config = FormConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': '表单配置不存在'
            }), 404
        
        user_id = session.get('user_id')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 权限检查
        if not can_manage_form and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权限发布表单配置'
            }), 403
        
        # 如果是类别管理员但不是超级管理员，检查是否有权限管理该类别
        if not is_super_admin and is_category_admin:
            if config.category_id not in category_ids:
                return jsonify({
                    'success': False,
                    'message': '无权限发布该表单配置'
                }), 403
        
        if config.status == 'published':
            return jsonify({
                'success': False,
                'message': '表单配置已发布'
            }), 400
        
        # 下架同类别其他已发布的配置
        existing = FormConfig.query.filter_by(
            category_id=config.category_id,
            status='published'
        ).all()
        for ex in existing:
            ex.status = 'archived'
        
        # 发布当前配置
        config.status = 'published'
        config.publish_time = datetime.now()
        config.update_time = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '表单配置发布成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"发布表单配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '发布表单配置失败'
        }), 500


@form_config_bp.route('/form-configs/<int:config_id>/archive', methods=['POST'])
@login_required
def archive_form_config(config_id):
    """
    下架表单配置
    超级管理员、can_manage_form权限的管理员、类别管理员都可以下架表单配置
    类别管理员只能下架自己管理的类别的表单配置
    """
    try:
        config = FormConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': '表单配置不存在'
            }), 404
        
        user_id = session.get('user_id')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 权限检查
        if not can_manage_form and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权限下架表单配置'
            }), 403
        
        # 如果是类别管理员但不是超级管理员，检查是否有权限管理该类别
        if not is_super_admin and is_category_admin:
            if config.category_id not in category_ids:
                return jsonify({
                    'success': False,
                    'message': '无权限下架该表单配置'
                }), 403
        
        # 下架：将状态改为草稿，以便可以编辑
        config.status = 'draft'
        config.update_time = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '表单配置下架成功，已转为草稿状态'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"下架表单配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '下架表单配置失败'
        }), 500


@form_config_bp.route('/form-configs/<int:config_id>', methods=['DELETE'])
@login_required
def delete_form_config(config_id):
    """
    删除表单配置（仅草稿状态可删除）
    超级管理员、can_manage_form权限的管理员、类别管理员都可以删除表单配置
    类别管理员只能删除自己管理的类别的表单配置
    """
    try:
        config = FormConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': '表单配置不存在'
            }), 404
        
        user_id = session.get('user_id')
        
        # 检查用户权限
        from models import AdminConfig, CategoryAdmin
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        can_manage_form = admin and (admin.is_super_admin or admin.can_manage_form)
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 权限检查
        if not can_manage_form and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权限删除表单配置'
            }), 403
        
        # 如果是类别管理员但不是超级管理员，检查是否有权限管理该类别
        if not is_super_admin and is_category_admin:
            if config.category_id not in category_ids:
                return jsonify({
                    'success': False,
                    'message': '无权限删除该表单配置'
                }), 403
        
        if config.status != 'draft':
            return jsonify({
                'success': False,
                'message': '只能删除草稿状态的表单配置'
            }), 400
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '表单配置删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除表单配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '删除表单配置失败'
        }), 500

