"""
工单管理路由
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime
import logging
import json
from urllib.parse import quote
from models import db, WorkOrder, WorkOrderFlow, CategoryConfig, Staff, AdminConfig, DepartmentAdmin, CategoryAdmin, FormConfig
from auth.decorators import login_required, permission_required
from notification.service import get_notification_service
from admin.routes import get_staff_by_cardno

logger = logging.getLogger(__name__)

work_order_bp = Blueprint('work_order', __name__)


@work_order_bp.route('/work-orders', methods=['GET'])
@login_required
def get_work_orders():
    """
    获取工单列表
    支持筛选：我申请的/待我审批的/我管理的
    """
    try:
        user_id = session.get('user_id')
        filter_type = request.args.get('filter', 'my_applications')  # my_applications/pending_approvals/my_managed
        status = request.args.get('status', '')
        category_id = request.args.get('category_id', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建查询
        query = WorkOrder.query
        
        if filter_type == 'pending_approvals':
            # 待我处理的工单（当前审批人是我，或者我是申请人且工单状态为已打回）
            # 排除external状态的工单（外派状态的工单不应该出现在待处理列表中）
            # 除非当前用户是外派操作人（通过检查是否有external action的flow记录）
            
            from sqlalchemy import or_
            
            # 查找当前用户外派的工单（external状态的工单，且action='external'的flow记录的action_user_id是当前用户）
            external_orders = db.session.query(WorkOrder.id).join(WorkOrderFlow).filter(
                WorkOrder.status == 'external',
                WorkOrderFlow.action == 'external',
                WorkOrderFlow.action_user_id == user_id
            ).distinct().all()
            external_order_ids = [order_id[0] for order_id in external_orders]
            
            # 查找已打回的工单（returned状态，且申请人是当前用户）
            returned_order_ids = []
            returned_orders = WorkOrder.query.filter(
                WorkOrder.status == 'returned',
                WorkOrder.applicant_id == user_id
            ).all()
            if returned_orders:
                returned_order_ids = [order.id for order in returned_orders]
            
            # 构建查询条件
            conditions = []
            
            # 条件1：普通的pending审批工单（排除external状态）
            # 需要join WorkOrderFlow来检查approver_id和to_status
            conditions.append(
                db.and_(
                    WorkOrderFlow.approver_id == user_id,
                    WorkOrderFlow.to_status == 'pending',
                    WorkOrder.status != 'external'
                )
            )
            
            # 条件2：当前用户外派的external状态工单
            if external_order_ids:
                conditions.append(WorkOrder.id.in_(external_order_ids))
            
            # 条件3：已打回的工单（申请人是当前用户）
            if returned_order_ids:
                conditions.append(WorkOrder.id.in_(returned_order_ids))
            
            # 执行查询
            # 如果条件中包含WorkOrderFlow的条件，需要join；否则不需要
            need_join_flow = len(conditions) > 1 or (len(conditions) == 1 and external_order_ids == [] and returned_order_ids == [])
            
            if need_join_flow:
                # 需要join WorkOrderFlow（有pending审批条件）
                if len(conditions) > 1:
                    # 多个条件，使用left join（因为条件2和3不需要flow表）
                    query = query.join(WorkOrderFlow, isouter=True).filter(
                        or_(*conditions)
                    ).distinct()
                else:
                    # 只有一个条件（pending审批）
                    query = query.join(WorkOrderFlow).filter(conditions[0]).distinct()
            else:
                # 不需要join WorkOrderFlow（只有已打回或外派的工单）
                if len(conditions) > 0:
                    query = query.filter(or_(*conditions)).distinct()
                else:
                    # 没有符合条件的工单
                    query = query.filter(WorkOrder.id == -1)  # 返回空结果
        elif filter_type == 'my_managed':
            # 我管理的工单（需要检查是否为管理员）
            admin = AdminConfig.query.filter_by(user_id=user_id).first()
            if admin and admin.is_super_admin:
                # 超级管理员可以看到所有工单
                pass
            else:
                # 类别管理员只能看到自己管理的类别
                category_ids = [ca.category_id for ca in CategoryAdmin.query.filter_by(admin_id=user_id).all()]
                if category_ids:
                    query = query.filter(WorkOrder.category_id.in_(category_ids))
                else:
                    query = query.filter(False)  # 无权限
        else:
            # 我申请的工单（包含撤单的工单）
            query = query.filter_by(applicant_id=user_id)
        
        # 排除撤单的工单（"我申请的"需要包含撤单工单，其他查询需要排除）
        if filter_type != 'my_applications':
            query = query.filter(WorkOrder.status != 'cancelled')
        
        if status:
            query = query.filter_by(status=status)
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        
        # 分页
        pagination = query.order_by(WorkOrder.create_time.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 格式化数据，并添加类别名称
        items = []
        for order in pagination.items:
            order_dict = order.to_dict()
            # 获取类别名称
            category = CategoryConfig.query.get(order.category_id)
            if category:
                order_dict['category_name'] = category.category_name
            items.append(order_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"获取工单列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取工单列表失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>', methods=['GET'])
@login_required
def get_work_order_detail(order_id):
    """获取工单详情"""
    try:
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        user_id = session.get('user_id')
        
        # 检查是否为当前审批人（用于后续判断is_current_approver）
        current_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            approver_id=user_id,
            to_status='pending'
        ).first()
        
        # 检查权限
        has_permission = False
        
        if order.applicant_id == user_id:
            # 申请人可以查看
            has_permission = True
        elif current_flow and current_flow.to_status == 'pending':
            # 当前审批人（to_status='pending'）可以查看
            has_permission = True
        elif order.status == 'external' and order.is_external:
            # 外派状态的工单，只有外派操作人可以查看
            external_flow = WorkOrderFlow.query.filter_by(
                work_order_id=order_id,
                action='external'
            ).order_by(WorkOrderFlow.create_time.desc()).first()
            if external_flow and external_flow.action_user_id == user_id:
                has_permission = True
        
        # 如果还没有权限，检查管理员权限
        if not has_permission:
            # 检查是否为超级管理员
            admin = AdminConfig.query.filter_by(user_id=user_id).first()
            if admin and admin.is_super_admin:
                # 超级管理员可以查看所有工单
                has_permission = True
            else:
                # 检查是否为该类别管理员（类别管理员可以查看自己管理的类别的工单）
                category_admin = CategoryAdmin.query.filter_by(
                    category_id=order.category_id,
                    admin_id=user_id
                ).first()
                if category_admin:
                    has_permission = True
        
        if not has_permission:
            return jsonify({
                'success': False,
                'message': '无权查看此工单'
            }), 403
        
        # 获取流转记录
        flows = WorkOrderFlow.query.filter_by(work_order_id=order_id).order_by(WorkOrderFlow.create_time).all()
        
        # 获取表单配置信息（用于前端显示表单项）
        form_config = None
        if order.form_config_id:
            from models import FormConfig
            form_config = FormConfig.query.get(order.form_config_id)
        
        order_dict = order.to_dict()
        if form_config:
            # 添加表单配置信息，包括字段配置
            order_dict['form_config'] = {
                'id': form_config.id,
                'name': form_config.name,
                'fields_config': form_config.get_fields_config(),
                'system_fields_order': form_config.get_system_fields_order()
            }
        else:
            # 如果没有form_config_id，尝试通过category_id查找
            if order.category_id:
                from models import FormConfig
                form_config = FormConfig.query.filter_by(
                    category_id=order.category_id,
                    status='published'
                ).first()
                if form_config:
                    order_dict['form_config'] = {
                        'id': form_config.id,
                        'name': form_config.name,
                        'fields_config': form_config.get_fields_config(),
                        'system_fields_order': form_config.get_system_fields_order()
                    }
        
        # 检查当前用户是否是当前审批人（用于前端显示审批/转派按钮）
        # 只有to_status='pending'的flow记录才表示是当前审批人
        is_current_approver = False
        if current_flow and current_flow.to_status == 'pending':
            is_current_approver = True
        
        # 检查当前用户是否是外派操作人（用于前端显示提交外派结果按钮）
        # 查找外派操作的flow记录（action='external'），检查当前用户是否是操作人
        is_external_operator = False
        if order.status == 'external' and order.is_external:
            external_flow = WorkOrderFlow.query.filter_by(
                work_order_id=order_id,
                action='external'
            ).order_by(WorkOrderFlow.create_time.desc()).first()
            if external_flow and external_flow.action_user_id == user_id:
                is_external_operator = True
        
        # 查找打回原因（如果工单状态是returned，查找action='return'的flow记录）
        return_reason = None
        return_comment = None
        if order.status == 'returned' and order.applicant_id == user_id:
            # 查找打回操作的flow记录（action='return'）
            return_flow = WorkOrderFlow.query.filter_by(
                work_order_id=order_id,
                action='return'
            ).order_by(WorkOrderFlow.create_time.desc()).first()
            if return_flow:
                return_reason = return_flow.comment or '工单已打回，请修改后重新提交'
                return_comment = return_flow.comment
        
        return jsonify({
            'success': True,
            'data': {
                'order': order_dict,
                'flows': [flow.to_dict() for flow in flows],
                'is_current_approver': is_current_approver,  # 是否是当前审批人
                'is_external_operator': is_external_operator,  # 是否是外派操作人
                'return_reason': return_reason,  # 打回原因
                'return_comment': return_comment  # 打回备注
            }
        })
    except Exception as e:
        logger.error(f"获取工单详情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取工单详情失败'
        }), 500


@work_order_bp.route('/work-orders', methods=['POST'])
@login_required
def create_work_order():
    """创建工单（保存草稿或提交）"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        user_dept = session.get('user_dept')
        user_phone = session.get('user_phone')
        user_email = session.get('user_email')
        
        action = data.get('action', 'submit')  # submit提交/draft保存草稿
        
        # 生成工单编号
        order_no = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id[-4:]}"
        
        # 创建工单
        order_status = 'draft' if action == 'draft' else 'pending'
        order = WorkOrder(
            order_no=order_no,
            category_id=data.get('category_id'),
            form_config_id=data.get('form_config_id'),
            applicant_id=user_id,
            applicant_name=user_name,
            applicant_dept=user_dept,
            applicant_phone=user_phone,
            applicant_email=user_email,
            apply_date=datetime.now().date(),
            assign_type=data.get('assign_type', 'individual'),
            assign_to_dept=data.get('assign_to_dept'),
            form_data=json.dumps(data.get('form_data', {}), ensure_ascii=False),
            status=order_status
        )
        
        db.session.add(order)
        db.session.flush()  # 获取order.id
        
        # 创建流转记录
        if action == 'draft':
            # 保存草稿：只创建流转记录，不分配和发送通知
            flow = WorkOrderFlow(
                work_order_id=order.id,
                action='create',
                action_user_id=user_id,
                action_user_name=user_name,
                from_status=None,
                to_status='draft',
                comment='工单保存为草稿'
            )
            db.session.add(flow)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '工单已保存为草稿',
                'data': {'id': order.id, 'order_no': order_no}
            })
        
        # 提交工单：创建流转记录并处理分配和通知
        flow = WorkOrderFlow(
            work_order_id=order.id,
            action='create',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status=None,
            to_status='pending',
            comment='工单创建并提交'
        )
        db.session.add(flow)
        
        # 处理分配和发送通知
        notification_service = get_notification_service()
        order_url = f"{current_app.config.get('FRONTEND_URL')}/work-orders/{order.id}"
        
        # 获取工单类别名称
        category = CategoryConfig.query.get(order.category_id)
        category_name = category.category_name if category else None
        
        if order.assign_type == 'individual':
            # 分配给个人
            approver_ids = data.get('approver_ids', [])
            for approver_id in approver_ids:
                # 使用get_staff_by_cardno获取审批人信息（包括phone和email）
                approver = get_staff_by_cardno(approver_id)
                if approver:
                    # 创建审批流转记录
                    approval_flow = WorkOrderFlow(
                        work_order_id=order.id,
                        action='assign',
                        action_user_id=user_id,
                        action_user_name=user_name,
                        from_status='pending',
                        to_status='pending',
                        approver_id=approver_id,
                        approver_name=approver.name,
                        comment=f'分配给 {approver.name} 审批'
                    )
                    db.session.add(approval_flow)
                    
                    # 发送通知（同时发送交我办通知和邮件通知）
                    # 注意：jAccount账号从email中提取（@字符之前的部分）
                    try:
                        notification_service.send_work_order_notification(
                            order_no=order_no,
                            action='new',
                            order_url=order_url,
                            phone=approver.phone,
                            email=approver.email,
                            applicant_name=user_name,
                            category_name=category_name
                        )
                    except Exception as e:
                        logger.error(f"发送工单通知失败: {e}", exc_info=True)
                        # 通知发送失败不影响工单创建
        else:
            # 分配给部门 - 群发通知给所有部门管理员
            dept_name = order.assign_to_dept
            dept_admins = DepartmentAdmin.query.filter_by(dept_name=dept_name).all()
            if dept_admins:
                # 收集所有部门管理员的信息
                admin_jaccounts = []  # jAccount账号（从email提取）
                admin_emails = []
                
                for dept_admin in dept_admins:
                    # 创建审批流转记录
                    approval_flow = WorkOrderFlow(
                        work_order_id=order.id,
                        action='assign',
                        action_user_id=user_id,
                        action_user_name=user_name,
                        from_status='pending',
                        to_status='pending',
                        approver_id=dept_admin.admin_id,
                        approver_name=dept_admin.admin_name,
                        comment=f'分配给部门 {dept_name} 管理员审批'
                    )
                    db.session.add(approval_flow)
                    
                    # 获取部门管理员详细信息（包括phone和email）
                    dept_admin_staff = get_staff_by_cardno(dept_admin.admin_id)
                    if dept_admin_staff and dept_admin_staff.email:
                        # 从email中提取jAccount账号（@字符之前的部分）
                        from notification.service import extract_jaccount_from_email
                        jaccount = extract_jaccount_from_email(dept_admin_staff.email)
                        if jaccount:
                            admin_jaccounts.append(jaccount)
                            admin_emails.append(dept_admin_staff.email)
                
                # 群发通知给所有部门管理员（同时发送交我办通知和邮件通知）
                if admin_jaccounts:
                    try:
                        # 获取前端URL（用于生成系统首页链接）
                        frontend_url = current_app.config.get('FRONTEND_URL')
                        
                        # 构建纯文本通知内容（用于app通知）
                        if category_name:
                            plain_content = f'{user_name} 提交的工单 {order_no}（类别：{category_name}）需要您审批'
                        else:
                            plain_content = f'{user_name} 提交的工单 {order_no} 需要您审批'
                        
                        # 构建HTML格式的邮件内容（带样式和链接）
                        greeting = "老师：您好！"
                        if category_name:
                            email_body = f'{user_name} 提交的工单 <strong>{order_no}</strong>（类别：<strong>{category_name}</strong>）需要您审批。'
                        else:
                            email_body = f'{user_name} 提交的工单 <strong>{order_no}</strong> 需要您审批。'
                        
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
                        
                        # 构建通知数据，支持批量发送
                        notification_data = {
                            'name': '新工单待审批',
                            'content': plain_content,  # 纯文本内容，用于app通知
                            'abstract': '新工单待审批',
                            'html': html_content,  # HTML格式内容，用于email通知
                            'accounts': admin_jaccounts,  # 使用jAccount账号（从email提取）
                            'channels': []
                        }
                        
                        # 构建App对象
                        app_data = {
                            'displayStyle': 'operation',
                            'abstract': '新工单待审批',
                            'content': [
                                {'name': '工单编号', 'value': order_no},
                                {'name': '申请人', 'value': user_name}
                            ]
                        }
                        
                        if category_name:
                            app_data['content'].append({'name': '工单类别', 'value': category_name})
                        
                        # 不再添加"操作"项
                        
                        if order_url:
                            app_data['urls'] = [{
                                'url': order_url,
                                'urlName': '查看详情',
                                'urlType': 'web'
                            }]
                        
                        notification_data['app'] = app_data
                        
                        # 添加渠道和收件人
                        if admin_jaccounts:
                            notification_data['channels'].append('app')
                        
                        if admin_emails:
                            notification_data['emails'] = admin_emails
                            notification_data['channels'].append('email')
                        
                        # 发送通知
                        notification_service.send_notification(notification_data)
                        logger.info(f"群发通知给部门 {dept_name} 的 {len(admin_jaccounts)} 位管理员成功")
                    except Exception as e:
                        logger.error(f"群发工单通知失败: {e}", exc_info=True)
                        # 通知发送失败不影响工单创建
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单提交成功',
            'data': {'id': order.id, 'order_no': order_no}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建工单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '创建工单失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>', methods=['PUT'])
@login_required
def update_work_order(order_id):
    """更新工单（仅草稿或已打回状态可更新）"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')

        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '工单不存在'}), 404

        if order.applicant_id != user_id:
            return jsonify({'success': False, 'message': '无权修改此工单'}), 403

        if order.status not in ['draft', 'returned']:
            return jsonify({'success': False, 'message': '只有草稿或已打回状态的工单可以修改'}), 400

        # 更新工单信息
        order.category_id = data.get('category_id', order.category_id)
        order.form_config_id = data.get('form_config_id', order.form_config_id)
        order.assign_type = data.get('assign_type', order.assign_type)
        order.assign_to_dept = data.get('assign_to_dept', order.assign_to_dept)
        order.form_data = json.dumps(data.get('form_data', {}), ensure_ascii=False)
        order.update_time = datetime.now()

        db.session.commit()
        return jsonify({'success': True, 'message': '工单更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新工单失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '更新工单失败'}), 500


@work_order_bp.route('/work-orders/<int:order_id>/submit', methods=['POST'])
@login_required
def submit_draft_work_order(order_id):
    """提交草稿或已打回的工单"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')

        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '工单不存在'}), 404

        if order.applicant_id != user_id:
            return jsonify({'success': False, 'message': '无权提交此工单'}), 403

        if order.status not in ['draft', 'returned']:
            return jsonify({'success': False, 'message': '只有草稿或已打回状态的工单可以提交'}), 400

        # 更新分配信息（如果提供了）
        assign_type = data.get('assign_type', order.assign_type)
        assign_to_dept = data.get('assign_to_dept', order.assign_to_dept)
        approver_ids = data.get('approver_ids', [])
        
        order.assign_type = assign_type
        order.assign_to_dept = assign_to_dept

        # 先保存当前状态，因为后面会改变order.status
        original_status = order.status
        
        # 更新创建流转记录的状态（如果是草稿）
        create_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            action='create',
            to_status='draft'
        ).first()
        if create_flow:
            create_flow.to_status = 'pending'
            create_flow.comment = '工单提交'
            db.session.add(create_flow)

        # 如果是打回状态，更新之前的return flow记录中的pending flow（如果有）
        if original_status == 'returned':
            return_flows = WorkOrderFlow.query.filter_by(
                work_order_id=order_id,
                action='return',
                to_status='pending'
            ).all()
            for flow in return_flows:
                flow.to_status = 'transferred'  # 标记为已处理
                db.session.add(flow)

        # 更新工单状态为pending
        order.status = 'pending'
        order.update_time = datetime.now()
        db.session.add(order)

        # 创建新的提交流转记录
        submit_flow = WorkOrderFlow(
            work_order_id=order_id,
            action='submit_draft',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status=original_status,  # 使用原始状态
            to_status='pending',
            comment='工单重新提交'
        )
        db.session.add(submit_flow)

        # 处理分配和发送通知（类似创建工单的逻辑）
        notification_service = get_notification_service()
        order_url = f"{current_app.config.get('FRONTEND_URL')}/work-orders/{order.id}"
        
        # 获取工单类别名称
        category = CategoryConfig.query.get(order.category_id)
        category_name = category.category_name if category else None

        if assign_type == 'individual':
            # 分配给个人
            if approver_ids:
                for approver_id in approver_ids:
                    approver_staff = get_staff_by_cardno(approver_id)
                    if approver_staff:
                        # 创建分配流转记录
                        assign_flow = WorkOrderFlow(
                            work_order_id=order_id,
                            action='assign',
                            action_user_id=user_id,
                            action_user_name=user_name,
                            from_status='pending',
                            to_status='pending',
                            approver_id=approver_id,
                            approver_name=approver_staff.name,
                            comment=f'分配给 {approver_staff.name}'
                        )
                        db.session.add(assign_flow)
                        
                        # 发送通知
                        try:
                            notification_service.send_work_order_notification(
                                order_no=order.order_no,
                                action='new',
                                order_url=order_url,
                                phone=approver_staff.phone,
                                email=approver_staff.email,
                                applicant_name=order.applicant_name,
                                category_name=category_name
                            )
                        except Exception as e:
                            logger.error(f"发送通知失败: {e}", exc_info=True)
        elif assign_type == 'department' and assign_to_dept:
            # 分配给部门
            dept_admins = DepartmentAdmin.query.filter_by(dept_name=assign_to_dept).all()
            if dept_admins:
                admin_ids = [da.admin_id for da in dept_admins]
                admin_staff_list = [get_staff_by_cardno(admin_id) for admin_id in admin_ids]
                admin_staff_list = [s for s in admin_staff_list if s]  # 过滤None
                
                if admin_staff_list:
                    # 为每个部门管理员创建分配流转记录
                    for admin_staff in admin_staff_list:
                        assign_flow = WorkOrderFlow(
                            work_order_id=order_id,
                            action='assign',
                            action_user_id=user_id,
                            action_user_name=user_name,
                            from_status='pending',
                            to_status='pending',
                            approver_id=admin_staff.cardno,
                            approver_name=admin_staff.name,
                            comment=f'分配给部门 {assign_to_dept} 管理员 {admin_staff.name}'
                        )
                        db.session.add(assign_flow)
                    
                    # 批量发送通知
                    try:
                        admin_emails = [s.email for s in admin_staff_list if s.email]
                        admin_jaccounts = [email.split('@')[0] for email in admin_emails if '@' in email]
                        
                        if admin_jaccounts:
                            # 构建通知内容
                            plain_content = f'{order.applicant_name} 提交的工单 {order.order_no}（类别：{category_name}）需要您审批' if category_name else f'{order.applicant_name} 提交的工单 {order.order_no} 需要您审批'
                            
                            greeting = "老师：您好！"
                            if category_name:
                                email_body = f'{order.applicant_name} 提交的工单 <strong>{order.order_no}</strong>（类别：<strong>{category_name}</strong>）需要您审批。'
                            else:
                                email_body = f'{order.applicant_name} 提交的工单 <strong>{order.order_no}</strong> 需要您审批。'
                            
                            frontend_url = current_app.config.get('FRONTEND_URL')
                            system_link = f'<a href="{frontend_url}" style="color: #409EFF; text-decoration: none;">审批系统</a>'
                            ending = f'请登录{system_link}查看。'
                            
                            html_content = f'''
                            <div style="font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333;">
                                <p style="margin: 0 0 15px 0;">{greeting}</p>
                                <p style="margin: 0 0 15px 0;">{email_body}</p>
                                <p style="margin: 15px 0 0 0; color: #666;">{ending}</p>
                            </div>
                            '''
                            
                            notification_data = {
                                'name': '新工单待审批',
                                'content': plain_content,
                                'abstract': '新工单待审批',
                                'html': html_content,
                                'accounts': admin_jaccounts,
                                'channels': ['app']
                            }
                            
                            app_data = {
                                'displayStyle': 'operation',
                                'abstract': '新工单待审批',
                                'content': [
                                    {'name': '工单编号', 'value': order.order_no},
                                    {'name': '申请人', 'value': order.applicant_name}
                                ]
                            }
                            
                            if category_name:
                                app_data['content'].append({'name': '工单类别', 'value': category_name})
                            
                            if order_url:
                                app_data['urls'] = [{
                                    'url': order_url,
                                    'urlName': '查看详情',
                                    'urlType': 'web'
                                }]
                            
                            notification_data['app'] = app_data
                            
                            if admin_emails:
                                notification_data['emails'] = admin_emails
                                notification_data['channels'].append('email')
                            
                            notification_service.send_notification(notification_data)
                            logger.info(f"群发通知给部门 {assign_to_dept} 的 {len(admin_jaccounts)} 位管理员成功")
                    except Exception as e:
                        logger.error(f"群发工单通知失败: {e}", exc_info=True)

        db.session.commit()
        return jsonify({'success': True, 'message': '工单提交成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交工单失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '提交工单失败'}), 500


@work_order_bp.route('/work-orders/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_work_order(order_id):
    """审批工单（批准/拒绝/打回）"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        action = data.get('action')  # approve/reject/return
        
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        # 检查权限（是否为当前审批人）
        current_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            approver_id=user_id,
            to_status='pending'
        ).order_by(WorkOrderFlow.create_time.desc()).first()
        
        if not current_flow:
            return jsonify({
                'success': False,
                'message': '无权审批此工单'
            }), 403
        
        # 检查状态
        if order.status != 'pending':
            return jsonify({
                'success': False,
                'message': '工单已审批，无法重复审批'
            }), 400
        
        # 如果工单是分配给部门的，需要将该部门所有管理员的pending flow记录都更新为completed
        # 这样其他部门管理员就不会再看到这条工单了
        if order.assign_type == 'department' and order.assign_to_dept:
            # 找到该部门的所有管理员ID
            dept_admin_ids = [da.admin_id for da in DepartmentAdmin.query.filter_by(dept_name=order.assign_to_dept).all()]
            
            # 找到该工单的所有pending flow记录，且审批人是该部门的管理员
            dept_pending_flows = WorkOrderFlow.query.filter(
                WorkOrderFlow.work_order_id == order_id,
                WorkOrderFlow.to_status == 'pending',
                WorkOrderFlow.approver_id.in_(dept_admin_ids)
            ).all()
            
            # 更新所有该部门的pending flow记录（包括当前操作人）
            for flow in dept_pending_flows:
                flow.to_status = 'completed'
                if flow.approver_id != user_id:
                    # 其他部门管理员的记录，添加备注说明
                    flow.comment = f'由 {user_name} 处理，其他部门管理员不再需要审批'
                db.session.add(flow)
        else:
            # 分配给个人的情况，只更新当前审批人的flow记录
            current_flow.to_status = 'completed'
            db.session.add(current_flow)
        
        # 更新工单状态
        from_status = order.status
        if action == 'approve':
            to_status = 'completed'
            order.status = 'completed'  # 已批准统一改为completed（已完成）
        elif action == 'reject':
            to_status = 'rejected'
            order.status = 'rejected'  # 已拒绝保持rejected状态
        elif action == 'return':
            to_status = 'returned'
            # 打回时，工单状态设置为returned（已打回），并创建一个新的pending flow记录给申请人
            order.status = 'returned'  # 打回后工单状态为returned（已打回），等待申请人重新提交
        else:
            return jsonify({
                'success': False,
                'message': '无效的操作类型'
            }), 400
        
        if action == 'approve':
            # 已批准（现在统一为completed）时，记录完成时间
            order.complete_time = datetime.now()
        
        order.update_time = datetime.now()
        
        # 创建流转记录
        flow = WorkOrderFlow(
            work_order_id=order_id,
            action=action,
            action_user_id=user_id,
            action_user_name=user_name,
            from_status=from_status,
            to_status=to_status,
            approver_id=user_id,
            approver_name=user_name,
            comment=data.get('comment', '')
        )
        db.session.add(flow)
        
        # 如果是打回操作，需要创建一个新的pending flow记录给申请人
        if action == 'return':
            # 创建pending flow记录，approver_id是申请人ID，这样申请人就能在待审批列表中看到
            return_flow = WorkOrderFlow(
                work_order_id=order_id,
                action='return',
                action_user_id=user_id,
                action_user_name=user_name,
                from_status='returned',
                to_status='pending',
                approver_id=order.applicant_id,  # 审批人是申请人
                approver_name=order.applicant_name,
                comment=f'工单已打回，等待申请人重新提交。打回原因：{data.get("comment", "")}'
            )
            db.session.add(return_flow)
        
        # 发送通知给申请人
        notification_service = get_notification_service()
        action_map = {
            'approve': 'approved',
            'reject': 'rejected',
            'return': 'returned'
        }
        notification_action = action_map.get(action, 'new')
        order_url = f"{current_app.config.get('FRONTEND_URL')}/work-orders/{order.id}"
        
        # 获取申请人信息（包括email和phone）
        applicant_staff = get_staff_by_cardno(order.applicant_id)
        # 获取工单类别名称
        category = CategoryConfig.query.get(order.category_id)
        category_name = category.category_name if category else None
        
        if applicant_staff:
            try:
                notification_service.send_work_order_notification(
                    order_no=order.order_no,
                    action=notification_action,
                    order_url=order_url,
                    phone=applicant_staff.phone,
                    email=applicant_staff.email,
                    applicant_name=order.applicant_name,
                    category_name=category_name
                )
            except Exception as e:
                logger.error(f"发送审批通知失败: {e}", exc_info=True)
                # 通知发送失败不影响审批操作
        
        db.session.commit()
        
        # 操作文本映射
        action_text_map = {
            'approve': '批准',
            'reject': '拒绝',
            'return': '打回'
        }
        action_text = action_text_map.get(action, '处理')
        
        return jsonify({
            'success': True,
            'message': f'工单{action_text}成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"审批工单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '审批工单失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>/transfer', methods=['POST'])
@login_required
def transfer_work_order(order_id):
    """转派工单"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        transfer_to_id = data.get('transfer_to_id')
        comment = data.get('comment', '')
        
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        # 检查权限（只有审批人可以转派）
        current_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            approver_id=user_id,
            to_status='pending'
        ).first()
        
        if not current_flow:
            return jsonify({
                'success': False,
                'message': '无权转派此工单'
            }), 403
        
        # 检查是否转派给自己
        if transfer_to_id == user_id:
            return jsonify({
                'success': False,
                'message': '不能转派给自己'
            }), 400
        
        # 获取转派对象信息（使用get_staff_by_cardno获取完整信息）
        transfer_to = get_staff_by_cardno(transfer_to_id)
        if not transfer_to:
            return jsonify({
                'success': False,
                'message': '转派对象不存在'
            }), 400
        
        # 如果工单是分配给部门的，需要将该部门所有管理员的pending flow记录都更新为transferred
        # 这样其他部门管理员就不会再看到这条工单了
        if order.assign_type == 'department' and order.assign_to_dept:
            # 找到该部门的所有管理员ID
            dept_admin_ids = [da.admin_id for da in DepartmentAdmin.query.filter_by(dept_name=order.assign_to_dept).all()]
            
            # 找到该工单的所有pending flow记录，且审批人是该部门的管理员
            dept_pending_flows = WorkOrderFlow.query.filter(
                WorkOrderFlow.work_order_id == order_id,
                WorkOrderFlow.to_status == 'pending',
                WorkOrderFlow.approver_id.in_(dept_admin_ids)
            ).all()
            
            # 更新所有该部门的pending flow记录
            for flow in dept_pending_flows:
                if flow.approver_id == user_id:
                    # 当前操作人的记录，更新为transferred，并记录转派信息
                    flow.to_status = 'transferred'
                    flow.transfer_to_id = transfer_to_id
                    flow.transfer_to_name = transfer_to.name
                    flow.comment = comment or f'转派给 {transfer_to.name}'
                else:
                    # 其他部门管理员的记录，也更新为transferred
                    flow.to_status = 'transferred'
                    flow.comment = f'由 {user_name} 转派给 {transfer_to.name}，其他部门管理员不再需要审批'
                db.session.add(flow)
        else:
            # 分配给个人的情况，只更新当前审批人的flow记录
            current_flow.to_status = 'transferred'
            current_flow.transfer_to_id = transfer_to_id
            current_flow.transfer_to_name = transfer_to.name
            current_flow.comment = comment or f'转派给 {transfer_to.name}'
            db.session.add(current_flow)
        
        # 创建新的转派流转记录（给新的审批人）
        new_flow = WorkOrderFlow(
            work_order_id=order_id,
            action='transfer',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status=order.status,
            to_status='pending',  # 新审批人的状态为pending
            approver_id=transfer_to_id,
            approver_name=transfer_to.name,
            transfer_to_id=transfer_to_id,
            transfer_to_name=transfer_to.name,
            comment=comment or f'由 {user_name} 转派给 {transfer_to.name}'
        )
        db.session.add(new_flow)
        
        # 发送通知给新的审批人（同时发送交我办通知和邮件通知）
        notification_service = get_notification_service()
        order_url = f"{current_app.config.get('FRONTEND_URL')}/work-orders/{order.id}"
        
        # 获取工单类别名称
        category = CategoryConfig.query.get(order.category_id)
        category_name = category.category_name if category else None
        
        try:
            # 注意：jAccount账号从email中提取（@字符之前的部分）
            notification_service.send_work_order_notification(
                order_no=order.order_no,
                action='transferred',
                order_url=order_url,
                phone=transfer_to.phone,
                email=transfer_to.email,
                applicant_name=order.applicant_name,
                category_name=category_name
            )
        except Exception as e:
            logger.error(f"发送转派通知失败: {e}", exc_info=True)
            # 通知发送失败不影响转派操作
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单转派成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"转派工单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '转派工单失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>/external', methods=['POST'])
@login_required
@permission_required('manage_external')
def external_work_order(order_id):
    """外派工单"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        # 检查当前用户是否是当前审批人（转派给别人的工单，原审批人不能再外派）
        current_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            approver_id=user_id,
            to_status='pending'
        ).first()
        
        if not current_flow:
            return jsonify({
                'success': False,
                'message': '无权外派此工单，只有当前审批人可以外派'
            }), 403
        
        # 更新外派信息
        order.is_external = True
        order.external_name = data.get('external_name')
        order.external_phone = data.get('external_phone')
        order.status = 'external'  # 外派状态
        order.update_time = datetime.now()
        db.session.add(order)  # 确保order对象被添加到session中
        
        # 更新所有pending的flow记录（其他审批人不再需要审批）
        pending_flows = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            to_status='pending'
        ).all()
        
        for pending_flow in pending_flows:
            if pending_flow.approver_id != user_id:
                # 其他审批人的flow记录状态改为transferred，表示已转出
                pending_flow.to_status = 'transferred'
                pending_flow.comment = f'由 {user_name} 外派，其他审批人不再需要审批'
                db.session.add(pending_flow)
            else:
                # 外派操作人自己的pending flow记录也更新为transferred
                pending_flow.to_status = 'transferred'
                db.session.add(pending_flow)
        
        # 创建流转记录
        # 如果有备注，使用备注；否则使用默认格式
        comment = data.get('comment', '').strip()
        if comment:
            flow_comment = f'外派给 {order.external_name} ({order.external_phone})，备注：{comment}'
        else:
            flow_comment = f'外派给 {order.external_name} ({order.external_phone})'
        
        flow = WorkOrderFlow(
            work_order_id=order_id,
            action='external',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status='pending',
            to_status='external',
            comment=flow_comment
        )
        db.session.add(flow)
        
        # 可选：发送短信通知
        if data.get('send_notification', False):
            notification_service = get_notification_service()
            notification_service.send_to_phone(
                order.external_phone,
                f'您有新的工单需要处理：{order.order_no}，联系电话：{order.applicant_phone or "系统"}'
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单外派成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"外派工单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '外派工单失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>/external/result', methods=['POST'])
@login_required
def submit_external_result(order_id):
    """提交外派结果"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        user_phone = session.get('user_phone')
        
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        if not order.is_external:
            return jsonify({
                'success': False,
                'message': '此工单未外派'
            }), 400
        
        # 检查权限：只有外派操作人（执行外派操作的用户）可以提交外派结果
        # 查找外派操作的flow记录（action='external'），检查当前用户是否是操作人
        external_flow = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            action='external'
        ).order_by(WorkOrderFlow.create_time.desc()).first()
        
        if not external_flow or external_flow.action_user_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权提交此工单的外派结果，只有外派操作人可以提交'
            }), 403
        
        # 更新外派结果
        external_result = data.get('result', '').strip()
        order.external_result = external_result
        order.status = 'completed'
        order.complete_time = datetime.now()
        order.update_time = datetime.now()
        db.session.add(order)  # 确保order对象被添加到session中
        
        # 创建流转记录，包含外派结果内容
        if external_result:
            flow_comment = f'外派结果已提交，工单完成。外派结果：{external_result}'
        else:
            flow_comment = '外派结果已提交，工单完成'
        
        flow = WorkOrderFlow(
            work_order_id=order_id,
            action='complete',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status='external',
            to_status='completed',
            comment=flow_comment
        )
        db.session.add(flow)
        
        # 发送通知给申请人
        notification_service = get_notification_service()
        order_url = f"{current_app.config.get('FRONTEND_URL')}/work-orders/{order.id}"
        
        # 获取申请人信息（包括email和phone）
        applicant_staff = get_staff_by_cardno(order.applicant_id)
        # 获取工单类别名称
        category = CategoryConfig.query.get(order.category_id)
        category_name = category.category_name if category else None
        
        if applicant_staff:
            try:
                notification_service.send_work_order_notification(
                    order_no=order.order_no,
                    action='completed',
                    order_url=order_url,
                    phone=applicant_staff.phone,
                    email=applicant_staff.email,
                    applicant_name=order.applicant_name,
                    category_name=category_name
                )
            except Exception as e:
                logger.error(f"发送完成通知失败: {e}", exc_info=True)
                # 通知发送失败不影响完成操作
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '外派结果提交成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交外派结果失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '提交外派结果失败'
        }), 500


@work_order_bp.route('/work-orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_work_order(order_id):
    """撤销工单（草稿、待处理、已打回状态可撤销）"""
    try:
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        
        order = WorkOrder.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': '工单不存在'
            }), 404
        
        # 检查权限：只有申请人可以撤销
        if order.applicant_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权撤销此工单，只有申请人可以撤销'
            }), 403
        
        # 检查状态：只有草稿、待处理、已打回状态的工单可以撤销
        if order.status not in ['draft', 'pending', 'returned']:
            return jsonify({
                'success': False,
                'message': f'工单状态为{order.status}，无法撤销。只有草稿、待处理、已打回状态的工单可以撤销'
            }), 400
        
        # 更新工单状态为已撤销
        from_status = order.status
        order.status = 'cancelled'
        order.update_time = datetime.now()
        
        # 更新所有pending状态的flow记录为cancelled
        pending_flows = WorkOrderFlow.query.filter_by(
            work_order_id=order_id,
            to_status='pending'
        ).all()
        
        for flow in pending_flows:
            flow.to_status = 'cancelled'
            flow.comment = f'工单已撤销，审批流程终止。原备注：{flow.comment or ""}'
            db.session.add(flow)
        
        # 创建撤销流转记录
        flow = WorkOrderFlow(
            work_order_id=order_id,
            action='cancel',
            action_user_id=user_id,
            action_user_name=user_name,
            from_status=from_status,
            to_status='cancelled',
            approver_id=user_id,
            approver_name=user_name,
            comment='工单已撤销'
        )
        db.session.add(flow)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '工单已撤销'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"撤销工单失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '撤销工单失败'
        }), 500


@work_order_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """
    获取Dashboard统计数据
    根据用户权限返回不同的统计数据：
    - 超级管理员：所有工单统计
    - 类别管理员：自己管理的类别的工单统计
    - 普通用户：自己申请的工单统计
    """
    try:
        user_id = session.get('user_id')
        category_id = request.args.get('category_id')  # 可选：按类别筛选
        
        # 检查是否为管理员
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        stats = {}
        query = WorkOrder.query
        
        # 如果指定了类别ID，进行筛选
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        
        if is_super_admin:
            # 超级管理员：查看所有工单（或指定类别的工单）
            # 统计口径：已完成、已拒绝、待处理、总工单数（排除撤单的工单）
            query = query.filter(WorkOrder.status != 'cancelled')  # 排除撤单的工单
            stats['total_orders'] = query.count()
            stats['pending_orders'] = query.filter_by(status='pending').count()  # 待处理（包括打回后变成pending的）
            stats['completed_orders'] = query.filter_by(status='completed').count()  # 已完成（包括原来的已批准）
            stats['rejected_orders'] = query.filter_by(status='rejected').count()  # 已拒绝
            stats['user_type'] = 'super_admin'
        elif is_category_admin:
            # 类别管理员：只看自己管理的类别的工单
            if category_id:
                # 如果指定了类别，检查是否有权限
                if int(category_id) not in category_ids:
                    return jsonify({
                        'success': False,
                        'message': '无权限查看该类别统计'
                    }), 403
                query = query.filter_by(category_id=int(category_id))
            else:
                # 未指定类别，统计所有管理的类别
                query = query.filter(WorkOrder.category_id.in_(category_ids))
            
            # 类别管理员：统计口径：已完成、已拒绝、待处理、总工单数（排除撤单的工单）
            # 待处理包括pending和returned状态的工单
            query = query.filter(WorkOrder.status != 'cancelled')  # 排除撤单的工单
            stats['total_orders'] = query.count()
            # 待处理 = pending + returned（打回的工单）
            stats['pending_orders'] = (
                query.filter_by(status='pending').count() +
                query.filter_by(status='returned').count()
            )
            stats['completed_orders'] = query.filter_by(status='completed').count()  # 已完成（包括原来的已批准）
            stats['rejected_orders'] = query.filter_by(status='rejected').count()  # 已拒绝
            stats['user_type'] = 'category_admin'
            stats['managed_categories'] = category_ids
        else:
            # 普通用户：只看自己的工单
            # 统计口径：已完成、已拒绝、待处理、总工单数（排除撤单的工单）
            # 待处理包括pending和returned状态的工单
            query = query.filter_by(applicant_id=user_id).filter(WorkOrder.status != 'cancelled')  # 排除撤单的工单
            stats['my_applications'] = query.count()  # 总工单数
            # 待处理 = pending + returned（打回的工单）
            stats['my_pending'] = (
                query.filter_by(status='pending').count() +
                query.filter_by(status='returned').count()
            )
            stats['my_completed'] = query.filter_by(status='completed').count()  # 已完成（包括原来的已批准）
            stats['my_rejected'] = query.filter_by(status='rejected').count()  # 已拒绝
            
            # 待我审批的工单（排除external状态的工单）
            approval_query = WorkOrderFlow.query.join(WorkOrder).filter(
                WorkOrderFlow.approver_id == user_id,
                WorkOrderFlow.to_status == 'pending',
                WorkOrder.status != 'external'  # 排除外派状态的工单
            )
            if category_id:
                # 如果指定了类别，需要关联工单表
                approval_query = approval_query.filter(
                    WorkOrder.category_id == int(category_id)
                )
            pending_count = approval_query.distinct().count()
            
            # 如果当前用户是外派操作人，需要加上external状态的工单数量
            external_count = WorkOrderFlow.query.join(WorkOrder).filter(
                WorkOrder.status == 'external',
                WorkOrderFlow.action == 'external',
                WorkOrderFlow.action_user_id == user_id
            )
            if category_id:
                external_count = external_count.filter(
                    WorkOrder.category_id == int(category_id)
                )
            external_count = external_count.distinct().count()
            
            stats['pending_approvals'] = pending_count + external_count
            stats['user_type'] = 'normal'
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取Dashboard统计失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取统计数据失败'
        }), 500


@work_order_bp.route('/work-orders/management', methods=['GET'])
@login_required
def get_work_orders_management():
    """
    工单管理页面接口（管理员使用）
    支持按类别、申请人、审批人等过滤查询
    """
    try:
        user_id = session.get('user_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 过滤条件
        category_id = request.args.get('category_id', '')
        applicant_id = request.args.get('applicant_id', '')
        approver_id = request.args.get('approver_id', '')
        status = request.args.get('status', '')
        order_no = request.args.get('order_no', '')
        
        # 检查权限：超级管理员或类别管理员都可以访问
        try:
            admin = AdminConfig.query.filter_by(user_id=user_id).first()
            is_super_admin = admin and admin.is_super_admin
            
            # 检查是否为类别管理员
            category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
            category_ids = [ca.category_id for ca in category_admins] if category_admins else []
            is_category_admin = len(category_ids) > 0
            
            # 既不是超级管理员，也不是类别管理员，则无权访问
            if not is_super_admin and not is_category_admin:
                logger.warning(f"用户 {user_id} 尝试访问工单管理页面，但不是管理员")
                return jsonify({
                    'success': False,
                    'message': '无权访问此页面，需要管理员权限'
                }), 403
        except Exception as e:
            logger.error(f"检查管理员权限失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'权限检查失败: {str(e)}'
            }), 500
        
        # 构建查询
        query = WorkOrder.query
        
        # 如果不是超级管理员，只能查看自己管理的类别
        if not is_super_admin:
            if category_ids:
                query = query.filter(WorkOrder.category_id.in_(category_ids))
            else:
                # 没有管理的类别，返回空结果
                query = query.filter(False)
        
        # 排除撤单的工单
        query = query.filter(WorkOrder.status != 'cancelled')
        
        # 应用过滤条件
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        if applicant_id:
            query = query.filter_by(applicant_id=applicant_id)
        if status:
            query = query.filter_by(status=status)
        if order_no:
            query = query.filter(WorkOrder.order_no.like(f'%{order_no}%'))
        
        # 如果指定了审批人，需要关联flow表
        if approver_id:
            query = query.join(WorkOrderFlow).filter(
                WorkOrderFlow.approver_id == approver_id
            ).distinct()
        
        # 分页
        pagination = query.order_by(WorkOrder.create_time.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 格式化数据，并添加类别名称和当前审批人信息
        items = []
        for order in pagination.items:
            order_dict = order.to_dict()
            # 获取类别名称
            category = CategoryConfig.query.get(order.category_id)
            if category:
                order_dict['category_name'] = category.category_name
            
            # 获取当前审批人信息
            current_flows = WorkOrderFlow.query.filter_by(
                work_order_id=order.id,
                to_status='pending'
            ).order_by(WorkOrderFlow.create_time.desc()).all()
            
            if current_flows:
                # 如果有多个pending的flow记录（部门分配的情况），显示所有审批人
                if len(current_flows) > 1:
                    # 部门分配的情况，显示所有审批人姓名，用逗号分隔
                    approver_names = []
                    for flow in current_flows:
                        if flow.approver_name:
                            approver_names.append(flow.approver_name)
                        elif flow.approver_id:
                            # 如果approver_name为空，从staff表查询
                            staff = get_staff_by_cardno(flow.approver_id)
                            if staff and staff.name:
                                approver_names.append(staff.name)
                            else:
                                approver_names.append(flow.approver_id)
                    order_dict['current_approver_id'] = ','.join([f.approver_id for f in current_flows if f.approver_id])
                    order_dict['current_approver_name'] = '、'.join(approver_names) if approver_names else None
                else:
                    # 单个审批人的情况
                    current_flow = current_flows[0]
                    order_dict['current_approver_id'] = current_flow.approver_id
                    if current_flow.approver_name:
                        order_dict['current_approver_name'] = current_flow.approver_name
                    elif current_flow.approver_id:
                        # 如果approver_name为空，从staff表查询
                        staff = get_staff_by_cardno(current_flow.approver_id)
                        if staff and staff.name:
                            order_dict['current_approver_name'] = staff.name
                        else:
                            order_dict['current_approver_name'] = current_flow.approver_id
                    else:
                        order_dict['current_approver_name'] = None
            else:
                # 如果没有pending的flow记录，可能是已审批完成或被转派
                # 尝试获取最后一条审批记录（非create和assign的action）
                last_approval_flow = WorkOrderFlow.query.filter(
                    WorkOrderFlow.work_order_id == order.id,
                    WorkOrderFlow.action.in_(['approve', 'reject', 'return', 'transfer'])
                ).order_by(WorkOrderFlow.create_time.desc()).first()
                
                if last_approval_flow:
                    # 如果是转派，显示转派给谁
                    if last_approval_flow.action == 'transfer' and last_approval_flow.transfer_to_name:
                        order_dict['current_approver_id'] = last_approval_flow.transfer_to_id
                        order_dict['current_approver_name'] = last_approval_flow.transfer_to_name
                    else:
                        # 显示最后审批的人
                        order_dict['current_approver_id'] = last_approval_flow.action_user_id
                        if last_approval_flow.action_user_name:
                            order_dict['current_approver_name'] = last_approval_flow.action_user_name
                        elif last_approval_flow.action_user_id:
                            staff = get_staff_by_cardno(last_approval_flow.action_user_id)
                            if staff and staff.name:
                                order_dict['current_approver_name'] = staff.name
                            else:
                                order_dict['current_approver_name'] = last_approval_flow.action_user_id
                        else:
                            order_dict['current_approver_name'] = None
                else:
                    order_dict['current_approver_id'] = None
                    order_dict['current_approver_name'] = None
            
            items.append(order_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"获取工单管理列表失败: {e}", exc_info=True)
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"详细错误堆栈: {error_detail}")
        return jsonify({
            'success': False,
            'message': f'获取工单列表失败: {str(e)}',
            'error_detail': error_detail if current_app.config.get('DEBUG') else None
        }), 500


@work_order_bp.route('/work-orders/export', methods=['GET'])
@login_required
def export_work_orders():
    """
    导出工单为Excel
    """
    logger.info("收到Excel导出请求")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from flask import Response
        import io
        
        user_id = session.get('user_id')
        
        # 检查权限：超级管理员或类别管理员都可以导出
        admin = AdminConfig.query.filter_by(user_id=user_id).first()
        is_super_admin = admin and admin.is_super_admin
        
        # 检查是否为类别管理员
        category_admins = CategoryAdmin.query.filter_by(admin_id=user_id).all()
        category_ids = [ca.category_id for ca in category_admins] if category_admins else []
        is_category_admin = len(category_ids) > 0
        
        # 既不是超级管理员，也不是类别管理员，则无权导出
        if not is_super_admin and not is_category_admin:
            return jsonify({
                'success': False,
                'message': '无权导出工单'
            }), 403
        
        # 获取过滤条件（与management接口相同）
        category_id = request.args.get('category_id', '')
        applicant_id = request.args.get('applicant_id', '')
        approver_id = request.args.get('approver_id', '')
        status = request.args.get('status', '')
        order_no = request.args.get('order_no', '')
        
        # 构建查询（与management接口相同）
        query = WorkOrder.query
        
        if not is_super_admin:
            if category_ids:
                query = query.filter(WorkOrder.category_id.in_(category_ids))
            else:
                query = query.filter(False)
        
        # 排除撤单的工单
        query = query.filter(WorkOrder.status != 'cancelled')
        
        if category_id:
            query = query.filter_by(category_id=int(category_id))
        if applicant_id:
            query = query.filter_by(applicant_id=applicant_id)
        if status:
            query = query.filter_by(status=status)
        if order_no:
            query = query.filter(WorkOrder.order_no.like(f'%{order_no}%'))
        if approver_id:
            query = query.join(WorkOrderFlow).filter(
                WorkOrderFlow.approver_id == approver_id
            ).distinct()
        
        # 获取所有符合条件的工单（不分页）
        orders = query.order_by(WorkOrder.create_time.desc()).all()
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = '工单列表'
        
        # 设置表头
        headers = ['工单编号', '类别', '申请人', '申请人部门', '状态', '当前审批人', '创建时间', '完成时间', '馆舍', '问题描述']
        ws.append(headers)
        
        # 设置表头样式
        header_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # 填充数据
        for order in orders:
            category = CategoryConfig.query.get(order.category_id)
            category_name = category.category_name if category else ''
            
            # 获取当前审批人信息（与management接口逻辑相同）
            current_flows = WorkOrderFlow.query.filter_by(
                work_order_id=order.id,
                to_status='pending'
            ).order_by(WorkOrderFlow.create_time.desc()).all()
            
            if current_flows:
                # 如果有多个pending的flow记录（部门分配的情况），显示所有审批人
                if len(current_flows) > 1:
                    approver_names = []
                    for flow in current_flows:
                        if flow.approver_name:
                            approver_names.append(flow.approver_name)
                        elif flow.approver_id:
                            staff = get_staff_by_cardno(flow.approver_id)
                            if staff and staff.name:
                                approver_names.append(staff.name)
                            else:
                                approver_names.append(flow.approver_id)
                    approver_name = '、'.join(approver_names) if approver_names else ''
                else:
                    # 单个审批人的情况
                    current_flow = current_flows[0]
                    if current_flow.approver_name:
                        approver_name = current_flow.approver_name
                    elif current_flow.approver_id:
                        staff = get_staff_by_cardno(current_flow.approver_id)
                        if staff and staff.name:
                            approver_name = staff.name
                        else:
                            approver_name = current_flow.approver_id
                    else:
                        approver_name = ''
            else:
                # 如果没有pending的flow记录，尝试获取最后一条审批记录
                last_approval_flow = WorkOrderFlow.query.filter(
                    WorkOrderFlow.work_order_id == order.id,
                    WorkOrderFlow.action.in_(['approve', 'reject', 'return', 'transfer'])
                ).order_by(WorkOrderFlow.create_time.desc()).first()
                
                if last_approval_flow:
                    if last_approval_flow.action == 'transfer' and last_approval_flow.transfer_to_name:
                        approver_name = last_approval_flow.transfer_to_name
                    else:
                        approver_name = last_approval_flow.action_user_name or ''
                else:
                    approver_name = ''
            
            status_text = {
                'pending': '待处理',
                'rejected': '已拒绝',
                'completed': '已完成',
                'terminated': '已终止',
                'external': '外派',
                'draft': '草稿',
                'cancelled': '已撤单',
                # 兼容旧数据
                'approved': '已完成',  # 旧数据：已批准 -> 已完成
                'returned': '待处理'    # 旧数据：已打回 -> 待处理
            }.get(order.status, order.status)
            
            # 解析form_data JSON，提取馆舍和问题描述
            building = ''
            description = ''
            
            # 获取表单配置，查找馆舍和问题描述字段的field_key
            form_config = None
            if order.form_config_id:
                form_config = FormConfig.query.get(order.form_config_id)
            elif order.category_id:
                # 如果没有form_config_id，尝试通过category_id查找已发布的表单配置
                form_config = FormConfig.query.filter_by(
                    category_id=order.category_id,
                    status='published'
                ).first()
            
            # 从表单配置中查找馆舍和问题描述字段的field_key
            building_field_key = None
            description_field_key = None
            if form_config:
                fields_config = form_config.get_fields_config()
                for field in fields_config:
                    field_label = field.get('field_label', '')
                    field_key = field.get('field_key', '')
                    # 查找馆舍字段
                    if '馆舍' in field_label and not building_field_key:
                        building_field_key = field_key
                    # 查找问题描述字段
                    if ('问题描述' in field_label or '问题说明' in field_label or '描述' in field_label) and not description_field_key:
                        description_field_key = field_key
            
            # 从form_data中提取数据
            if order.form_data:
                try:
                    form_data_dict = json.loads(order.form_data) if isinstance(order.form_data, str) else order.form_data
                    
                    # 使用field_key提取馆舍数据
                    if building_field_key:
                        building = form_data_dict.get(building_field_key, '')
                    else:
                        # 如果没有找到field_key，尝试直接使用字段名
                        building = form_data_dict.get('馆舍') or form_data_dict.get('building') or form_data_dict.get('馆舍名称') or ''
                    
                    # 使用field_key提取问题描述数据
                    if description_field_key:
                        description = form_data_dict.get(description_field_key, '')
                    else:
                        # 如果没有找到field_key，尝试直接使用字段名
                        description = form_data_dict.get('问题描述') or form_data_dict.get('description') or form_data_dict.get('问题说明') or form_data_dict.get('描述') or ''
                    
                    # 如果building或description是列表，转换为字符串
                    if isinstance(building, list):
                        building = ', '.join(str(x) for x in building)
                    if isinstance(description, list):
                        description = ', '.join(str(x) for x in description)
                    # 转换为字符串（处理None值）
                    building = str(building) if building else ''
                    description = str(description) if description else ''
                except Exception as e:
                    logger.warning(f"解析工单{order.order_no}的form_data失败: {e}")
                    building = ''
                    description = ''
            
            row = [
                order.order_no,
                category_name,
                order.applicant_name,
                order.applicant_dept or '',
                status_text,
                approver_name,
                order.create_time.strftime('%Y-%m-%d %H:%M:%S') if order.create_time else '',
                order.complete_time.strftime('%Y-%m-%d %H:%M:%S') if order.complete_time else '',
                building,
                description
            ]
            ws.append(row)
        
        # 调整列宽（新增馆舍和问题描述两列）
        column_widths = [20, 15, 15, 20, 10, 15, 20, 20, 15, 30]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        # 保存到内存
        output = io.BytesIO()
        try:
            wb.save(output)
            output.seek(0)
            logger.info(f"Excel文件已生成，大小: {len(output.getvalue())} 字节")
        except Exception as e:
            logger.error(f"保存Excel文件失败: {e}", exc_info=True)
            raise
        
        # 返回Excel文件
        filename = f'工单列表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        logger.info(f"Excel导出成功，文件名: {filename}, 工单数量: {len(orders)}")
        
        # 对文件名进行URL编码，以支持中文文件名
        # RFC 5987格式：filename*=UTF-8''encoded_filename
        encoded_filename = quote(filename.encode('utf-8'))
        content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': content_disposition,
                'Content-Length': str(len(output.getvalue()))
            }
        )
    except ImportError:
        logger.error("openpyxl未安装，无法导出Excel")
        return jsonify({
            'success': False,
            'message': 'Excel导出功能需要安装openpyxl库'
        }), 500
    except Exception as e:
        logger.error(f"导出工单失败: {e}", exc_info=True)
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'导出工单失败: {str(e)}'
        }), 500

