<template>
  <div class="work-order-detail">
    <div class="page-header">
      <h2>工单详情</h2>
      <el-button 
        icon="el-icon-back" 
        size="small"
        @click="goBack"
        style="background-color: #f5f7fa; border-color: #dcdfe6; color: #606266;"
      >
        返回
      </el-button>
    </div>
    <el-card>
      <div v-loading="loading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="工单编号">{{ order.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(order.status)">
              {{ getStatusText(order.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请人">{{ order.applicant_name }}</el-descriptions-item>
          <el-descriptions-item label="申请日期">{{ formatDate(order.apply_date) }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 打回原因提示（如果是已打回的工单且申请人是当前用户） -->
        <el-alert
          v-if="order.status === 'returned' && isApplicant && returnReason"
          type="warning"
          :closable="false"
          style="margin-top: 20px; margin-bottom: 20px;"
        >
          <div slot="title">
            <strong>工单已打回</strong>
          </div>
          <div slot="default">
            <p style="margin: 5px 0;"><strong>打回原因：</strong>{{ returnReason }}</p>
            <p style="margin: 5px 0; color: #606266;">请修改工单信息后重新提交。</p>
          </div>
        </el-alert>
        
        <!-- 表单项信息 -->
        <el-divider v-if="formFields.length > 0">工单信息</el-divider>
        <el-descriptions v-if="formFields.length > 0" :column="2" border>
          <el-descriptions-item
            v-for="field in formFields"
            :key="field.field_key"
            :label="field.field_label"
          >
            <div v-if="field.field_type === 'image' && getFieldValue(field.field_key)">
              <el-image
                v-for="(url, index) in getImageUrls(field.field_key)"
                :key="index"
                :src="getImageUrl(url)"
                :preview-src-list="getImagePreviewList(field.field_key)"
                style="width: 100px; height: 100px; margin-right: 10px;"
                fit="cover"
              ></el-image>
            </div>
            <div v-else-if="field.field_type === 'file' && getFieldValue(field.field_key)">
              <a
                :href="getFileUrl(getFieldValue(field.field_key))"
                target="_blank"
                style="color: #409EFF; text-decoration: none;"
              >
                {{ getFileName(getFieldValue(field.field_key)) }}
              </a>
            </div>
            <span v-else>{{ formatFieldValue(field) }}</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 外派信息 -->
        <el-divider v-if="order.is_external">外派信息</el-divider>
        <el-descriptions v-if="order.is_external" :column="2" border>
          <el-descriptions-item label="外派人员姓名">{{ order.external_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="外派人员电话">{{ order.external_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="order.external_result" label="外派结果" :span="2">
            <div style="white-space: pre-wrap; word-break: break-word;">{{ order.external_result }}</div>
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>流转记录</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="flow in displayFlows"
            :key="flow.id"
            :timestamp="flow.create_time"
          >
            <div>
              <div><strong>{{ getFlowActionText(flow.action) }}</strong></div>
              <div v-if="flow.action_user_name">操作人：{{ flow.action_user_name }}</div>
              <div v-if="flow.transfer_to_name">转派给：{{ flow.transfer_to_name }}</div>
              <div v-if="flow.comment" style="margin-top: 5px; color: #606266;">{{ flow.comment }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
        
        <!-- 从工单管理页面进入时不显示操作按钮 -->
        <template v-if="!isFromManagement">
          <el-divider>操作</el-divider>
          <!-- 如果申请人和审批人是同一人，且是当前审批人，优先显示审批操作 -->
          <template v-if="isApplicant && isCurrentApprover && order.status === 'pending'">
            <!-- 审批人操作（申请人和审批人是同一人时） -->
            <el-button 
              v-if="canApprove" 
              type="success" 
              @click="showApproveDialog = true"
            >
              审批
            </el-button>
            <el-button 
              v-if="canTransfer" 
              @click="showTransferDialog = true"
            >
              转派
            </el-button>
            <el-button 
              v-if="canExternal" 
              type="warning"
              @click="showExternalDialog = true"
            >
              外派
            </el-button>
            <el-button 
              v-if="canCancel" 
              type="danger"
              @click="handleCancel"
            >
              撤销
            </el-button>
          </template>
          <!-- 申请人操作（草稿或已打回状态，且不是当前审批人） -->
          <template v-else-if="isApplicant">
            <el-button 
              v-if="canEdit" 
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-button 
              v-if="canSubmit" 
              type="primary"
              @click="handleSubmit"
            >
              提交
            </el-button>
            <el-button 
              v-if="canCancel" 
              type="danger"
              @click="handleCancel"
            >
              撤销
            </el-button>
          </template>
          <!-- 审批人操作（不是申请人） -->
          <template v-else>
            <el-button 
              v-if="canApprove" 
              type="success" 
              @click="showApproveDialog = true"
            >
              审批
            </el-button>
            <el-button 
              v-if="canTransfer" 
              @click="showTransferDialog = true"
            >
              转派
            </el-button>
            <el-button 
              v-if="canExternal" 
              type="warning"
              @click="showExternalDialog = true"
            >
              外派
            </el-button>
            <el-button 
              v-if="canSubmitExternalResult" 
              type="primary"
              @click="showExternalResultDialog = true"
            >
              提交外派结果
            </el-button>
          </template>
        </template>
      </div>
    </el-card>
    
    <!-- 审批对话框 -->
    <el-dialog title="审批工单" :visible.sync="showApproveDialog">
      <el-form :model="approveForm">
        <el-form-item label="操作">
          <el-radio-group v-model="approveForm.action">
            <el-radio label="approve">批准</el-radio>
            <el-radio label="reject">拒绝</el-radio>
            <el-radio label="return">打回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="approveForm.comment" type="textarea"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleApprove">确定</el-button>
      </div>
    </el-dialog>
    
    <!-- 外派对话框 -->
    <el-dialog title="外派工单" :visible.sync="showExternalDialog">
      <el-form :model="externalForm" :rules="externalRules" ref="externalForm">
        <el-form-item label="外派人员姓名" prop="external_name">
          <el-input v-model="externalForm.external_name" placeholder="请输入外派人员姓名"></el-input>
        </el-form-item>
        <el-form-item label="外派人员电话" prop="external_phone">
          <el-input v-model="externalForm.external_phone" placeholder="请输入外派人员电话"></el-input>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="externalForm.comment" type="textarea" placeholder="可选"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showExternalDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExternal" :loading="externalSubmitting">确定</el-button>
      </div>
    </el-dialog>
    
    <!-- 提交外派结果对话框 -->
    <el-dialog title="提交外派结果" :visible.sync="showExternalResultDialog">
      <el-form :model="externalResultForm" :rules="externalResultRules" ref="externalResultForm">
        <el-form-item label="外派结果" prop="result">
          <el-input 
            v-model="externalResultForm.result" 
            type="textarea" 
            :rows="6"
            placeholder="请输入外派处理结果"
          ></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showExternalResultDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitExternalResult" :loading="externalResultSubmitting">确定</el-button>
      </div>
    </el-dialog>
    
    <!-- 转派对话框 -->
    <el-dialog title="转派工单" :visible.sync="showTransferDialog">
      <el-form :model="transferForm">
        <el-form-item label="转派给">
          <el-select
            v-model="transferForm.transfer_to_id"
            filterable
            remote
            :remote-method="searchStaff"
            :loading="staffSearchLoading"
            placeholder="请输入姓名或学工号搜索"
            style="width: 100%"
          >
            <el-option
              v-for="staff in staffList"
              :key="staff.id"
              :label="`${staff.name} (${staff.cardno || staff.code})`"
              :value="staff.cardno || staff.code"
            >
              <span>{{ staff.name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px;">
                {{ staff.cardno || staff.code }} - {{ staff.depart || staff.dept }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="transferForm.comment" type="textarea" placeholder="请输入转派原因"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button type="primary" @click="handleTransfer">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getWorkOrderDetail, approveWorkOrder, transferWorkOrder, externalWorkOrder, submitExternalResult, updateWorkOrder, submitDraftWorkOrder, cancelWorkOrder } from '@/api/workOrder'
import { searchStaff } from '@/api/admin'
import { mapState } from 'vuex'

export default {
  name: 'WorkOrderDetail',
  data() {
    return {
      loading: false,
      order: {},
      flows: [],
      formConfig: null,
      formData: {},
      isCurrentApprover: false,  // 是否是当前审批人
      isExternalOperator: false,  // 是否是外派操作人
      returnReason: null,  // 打回原因
      showApproveDialog: false,
      showTransferDialog: false,
      showExternalDialog: false,
      showExternalResultDialog: false,
      isFromManagement: false,  // 是否从工单管理页面进入
      approveForm: {
        action: 'approve',
        comment: ''
      },
      transferForm: {
        transfer_to_id: '',
        comment: ''
      },
      externalForm: {
        external_name: '',
        external_phone: '',
        comment: ''
      },
      externalRules: {
        external_name: [
          { required: true, message: '请输入外派人员姓名', trigger: 'blur' }
        ],
        external_phone: [
          { required: true, message: '请输入外派人员电话', trigger: 'blur' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
        ]
      },
      externalSubmitting: false,
      externalResultForm: {
        result: ''
      },
      externalResultRules: {
        result: [
          { required: true, message: '请输入外派结果', trigger: 'blur' }
        ]
      },
      externalResultSubmitting: false,
      staffList: [],
      staffSearchLoading: false
    }
  },
  computed: {
    ...mapState('user', ['user_id']),
    isApplicant() {
      return this.order.applicant_id === this.user_id
    },
    canEdit() {
      // 申请人可以编辑草稿或已打回的工单
      return this.isApplicant && (this.order.status === 'draft' || this.order.status === 'returned')
    },
    canSubmit() {
      // 申请人只能提交草稿状态的工单（已打回的工单需要先编辑再提交）
      return this.isApplicant && this.order.status === 'draft'
    },
    canCancel() {
      // 申请人可以撤销草稿、待处理或已打回的工单
      return this.isApplicant && ['draft', 'pending', 'returned'].includes(this.order.status)
    },
    formFields() {
      // 如果没有表单配置，返回空数组
      if (!this.formConfig) {
        return []
      }
      
      // 合并系统字段和自定义字段，按sort_order排序
      const systemFields = this.getSystemFields()
      const customFields = this.formConfig.fields_config || []
      
      // 合并并排序
      const allFields = [...systemFields, ...customFields]
      return allFields.sort((a, b) => {
        const orderA = a.sort_order || 0
        const orderB = b.sort_order || 0
        return orderA - orderB
      })
    },
    displayFlows() {
      // 合并相同的flow记录（特别是部门分配的记录）
      if (!this.flows || this.flows.length === 0) {
        return []
      }
      
      const otherFlows = [] // 非部门分配的其他记录
      const assignFlowMap = new Map() // 用于存储部门分配的flow记录
      
      for (const flow of this.flows) {
        // 对于assign操作，如果是分配给部门的，合并相同的记录
        if (flow.action === 'assign' && flow.comment && flow.comment.includes('分配给部门')) {
          // 使用comment和create_time作为唯一键
          const key = `${flow.action}_${flow.comment}_${flow.create_time}`
          
          if (!assignFlowMap.has(key)) {
            // 创建合并后的flow记录
            const mergedFlow = {
              ...flow,
              approver_names: [flow.approver_name].filter(Boolean) // 收集审批人姓名
            }
            assignFlowMap.set(key, mergedFlow)
          } else {
            // 如果已存在，添加审批人姓名到列表中
            const existingFlow = assignFlowMap.get(key)
            if (flow.approver_name && !existingFlow.approver_names.includes(flow.approver_name)) {
              existingFlow.approver_names.push(flow.approver_name)
            }
          }
        } else {
          // 其他操作直接添加
          otherFlows.push(flow)
        }
      }
      
      // 将合并后的部门分配记录添加到结果中
      const mergedFlows = []
      for (const mergedFlow of assignFlowMap.values()) {
        // 如果有多个审批人，更新comment显示所有审批人
        if (mergedFlow.approver_names.length > 1) {
          mergedFlow.comment = `${mergedFlow.comment}（审批人：${mergedFlow.approver_names.join('、')}）`
        }
        mergedFlows.push(mergedFlow)
      }
      
      // 合并所有记录
      const allFlows = [...otherFlows, ...mergedFlows]
      
      // 按时间排序
      return allFlows.sort((a, b) => {
        const timeA = new Date(a.create_time).getTime()
        const timeB = new Date(b.create_time).getTime()
        return timeA - timeB
      })
    },
    canApprove() {
      // 只有工单状态为pending且当前用户是审批人时才能审批
      return this.order.status === 'pending' && this.isCurrentApprover
    },
    canTransfer() {
      // 只有工单状态为pending且当前用户是审批人时才能转派
      return this.order.status === 'pending' && this.isCurrentApprover
    },
    canExternal() {
      // 只有工单状态为pending、当前用户是当前审批人且有外派权限时才能外派
      // 转派给别人的工单，原审批人不能再外派
      return this.order.status === 'pending' && this.isCurrentApprover && this.$store.state.user.can_manage_external
    },
    canSubmitExternalResult() {
      // 只有工单状态为external且当前用户是外派操作人时才能提交外派结果
      return this.order.status === 'external' && this.order.is_external && this.isExternalOperator
    }
  },
  mounted() {
    // 检查是否从工单管理页面进入
    this.isFromManagement = this.$route.query.from === 'management'
    this.loadDetail()
  },
  methods: {
    goBack() {
      // 根据来源页面决定返回位置
      if (this.isFromManagement) {
        // 从工单管理页面进入，返回工单管理页面
        this.$router.push('/work-orders/management')
      } else {
        // 从待我处理或我的申请进入，返回工单列表页面
        const filter = this.$route.query.filter || 'pending_approvals'
        this.$router.push({
          path: '/work-orders',
          query: { filter }
        })
      }
    },
    async loadDetail() {
      this.loading = true
      try {
        const res = await getWorkOrderDetail(this.$route.params.id)
        if (res.success) {
          this.order = res.data.order
          this.flows = res.data.flows
          this.isCurrentApprover = res.data.is_current_approver || false
          this.isExternalOperator = res.data.is_external_operator || false
          this.returnReason = res.data.return_reason || res.data.return_comment || null
          
          // 解析表单数据和配置
          if (this.order.form_data) {
            try {
              this.formData = typeof this.order.form_data === 'string' 
                ? JSON.parse(this.order.form_data) 
                : this.order.form_data
            } catch (e) {
              this.formData = {}
            }
          }
          
          if (this.order.form_config) {
            this.formConfig = this.order.form_config
          } else {
            // 如果没有form_config，尝试从form_config_id获取
            this.formConfig = null
          }
          
          // 调试信息
          console.log('工单详情数据:', {
            order: this.order,
            formConfig: this.formConfig,
            formData: this.formData,
            formFields: this.formFields,
            isCurrentApprover: this.isCurrentApprover
          })
        }
      } catch (error) {
        this.$message.error('加载工单详情失败')
      } finally {
        this.loading = false
      }
    },
    getSystemFields() {
      // 系统字段定义（不包含日期字段）
      return [
        { field_key: 'applicant_name', field_label: '申请人姓名', field_type: 'text', is_system: true, sort_order: 1 },
        { field_key: 'applicant_id', field_label: '申请人学工号', field_type: 'text', is_system: true, sort_order: 2 },
        { field_key: 'applicant_dept', field_label: '申请人部门', field_type: 'text', is_system: true, sort_order: 3 },
        { field_key: 'user_type', field_label: '身份类型', field_type: 'text', is_system: true, sort_order: 4 },
        { field_key: 'applicant_phone', field_label: '申请人手机号', field_type: 'text', is_system: true, sort_order: 5 },
        { field_key: 'applicant_email', field_label: '申请人邮箱', field_type: 'text', is_system: true, sort_order: 6 }
      ]
    },
    getFieldValue(fieldKey) {
      // 系统字段从order中获取（不包含日期字段）
      if (fieldKey === 'applicant_name') return this.order.applicant_name
      if (fieldKey === 'applicant_id') return this.order.applicant_id
      if (fieldKey === 'applicant_dept') return this.order.applicant_dept
      // 日期字段不再显示
      // if (fieldKey === 'apply_date') return this.order.apply_date
      // if (fieldKey === 'apply_time') return this.order.create_time
      if (fieldKey === 'user_type') return this.order.user_type || '教职工'
      if (fieldKey === 'applicant_phone') return this.order.applicant_phone
      if (fieldKey === 'applicant_email') return this.order.applicant_email
      
      // 自定义字段从formData中获取
      return this.formData[fieldKey]
    },
    formatFieldValue(field) {
      const value = this.getFieldValue(field.field_key)
      if (value === null || value === undefined || value === '') {
        return '-'
      }
      
      // 根据字段类型格式化显示
      if (field.field_type === 'select' || field.field_type === 'radio') {
        // 如果是选项类型，尝试从选项中匹配显示文本
        if (field.field_options && Array.isArray(field.field_options)) {
          const option = field.field_options.find(opt => opt.value === value || opt === value)
          return option ? (option.label || option) : value
        }
      }
      
      if (field.field_type === 'checkbox') {
        // 复选框返回数组
        if (Array.isArray(value)) {
          if (field.field_options && Array.isArray(field.field_options)) {
            return value.map(v => {
              const option = field.field_options.find(opt => opt.value === v || opt === v)
              return option ? (option.label || option) : v
            }).join('、')
          }
          return value.join('、')
        }
      }
      
      if (field.field_type === 'date' || field.field_type === 'datetime') {
        // 日期格式化：统一为yyyy-MM-dd格式
        if (value) {
          const date = new Date(value)
          if (isNaN(date.getTime())) {
            return value // 如果无法解析，返回原值
          }
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          if (field.field_type === 'date') {
            return `${year}-${month}-${day}`
          } else {
            // datetime格式：yyyy-MM-dd HH:mm:ss
            const hours = String(date.getHours()).padStart(2, '0')
            const minutes = String(date.getMinutes()).padStart(2, '0')
            const seconds = String(date.getSeconds()).padStart(2, '0')
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
          }
        }
      }
      
      return value
    },
    getImageUrls(fieldKey) {
      const value = this.getFieldValue(fieldKey)
      if (!value) return []
      if (Array.isArray(value)) return value
      if (typeof value === 'string') {
        try {
          const parsed = JSON.parse(value)
          return Array.isArray(parsed) ? parsed : [value]
        } catch {
          return [value]
        }
      }
      return []
    },
    getImageUrl(url) {
      if (!url) return ''
      // 如果是完整的HTTP/HTTPS URL，直接返回
      if (url.startsWith('http://') || url.startsWith('https://')) return url
      // 如果URL已经包含/process前缀，直接使用
      if (url.startsWith('/process')) return url
      // 如果URL以/开头（但不包含/process），添加/process前缀
      if (url.startsWith('/')) return `/process${url}`
      // 否则，假设是相对路径，添加/process/uploads/images/前缀
      // 注意：根据上传接口，图片存储在uploads/images/目录下
      return `/process/uploads/images/${url}`
    },
    getImagePreviewList(fieldKey) {
      return this.getImageUrls(fieldKey).map(url => this.getImageUrl(url))
    },
    getFileUrl(value) {
      if (!value) return ''
      if (typeof value === 'string') {
        if (value.startsWith('http://') || value.startsWith('https://')) return value
        if (value.startsWith('/process')) return value
        if (value.startsWith('/')) return `/process${value}`
        // 假设是相对路径，添加/process/uploads/files/前缀
        return `/process/uploads/files/${value}`
      }
      if (value.url) {
        if (value.url.startsWith('http://') || value.url.startsWith('https://')) return value.url
        if (value.url.startsWith('/process')) return value.url
        if (value.url.startsWith('/')) return `/process${value.url}`
        return `/process/uploads/files/${value.url}`
      }
      return ''
    },
    getFileName(value) {
      if (!value) return ''
      if (typeof value === 'string') {
        return value.split('/').pop() || value
      }
      if (value.name) return value.name
      if (value.url) return value.url.split('/').pop() || value.url
      return ''
    },
    formatDate(dateStr) {
      // 统一日期格式为yyyy-MM-dd
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return dateStr
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    async handleApprove() {
      try {
        const res = await approveWorkOrder(this.order.id, this.approveForm)
        if (res.success) {
          this.$message.success('审批成功')
          this.showApproveDialog = false
          // 审批成功后跳转回待我处理页面
          this.$router.push({
            path: '/work-orders',
            query: { filter: 'pending_approvals' }
          })
        }
      } catch (error) {
        this.$message.error('审批失败')
      }
    },
    async handleTransfer() {
      if (!this.transferForm.transfer_to_id) {
        this.$message.warning('请选择转派对象')
        return
      }
      
      // 检查是否转派给自己
      const currentUserId = this.$store.state.user.user_id
      if (this.transferForm.transfer_to_id === currentUserId) {
        this.$message.warning('不能转派给自己')
        return
      }
      
      try {
        const res = await transferWorkOrder(this.order.id, this.transferForm)
        if (res.success) {
          this.$message.success('转派成功')
          this.showTransferDialog = false
          this.transferForm = {
            transfer_to_id: '',
            comment: ''
          }
          // 转派成功后跳转回待我处理页面
          this.$router.push({
            path: '/work-orders',
            query: { filter: 'pending_approvals' }
          })
        }
      } catch (error) {
        // 如果后端返回了错误信息，显示后端错误信息
        if (error.response && error.response.data && error.response.data.message) {
          this.$message.error(error.response.data.message)
        } else {
          this.$message.error('转派失败')
        }
      }
    },
    async handleExternal() {
      // 表单验证
      this.$refs.externalForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.externalSubmitting = true
        try {
          const res = await externalWorkOrder(this.order.id, {
            external_name: this.externalForm.external_name,
            external_phone: this.externalForm.external_phone,
            comment: this.externalForm.comment
          })
          
          if (res.success) {
            this.$message.success('外派成功')
            this.showExternalDialog = false
            this.externalForm = {
              external_name: '',
              external_phone: '',
              comment: ''
            }
            // 重新加载工单详情
            this.loadDetail()
          } else {
            this.$message.error(res.message || '外派失败')
          }
        } catch (error) {
          // 如果后端返回了错误信息，显示后端错误信息
          if (error.response && error.response.data && error.response.data.message) {
            this.$message.error(error.response.data.message)
          } else {
            this.$message.error('外派失败')
          }
        } finally {
          this.externalSubmitting = false
        }
      })
    },
    async handleSubmitExternalResult() {
      // 表单验证
      this.$refs.externalResultForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.externalResultSubmitting = true
        try {
          const res = await submitExternalResult(this.order.id, {
            result: this.externalResultForm.result
          })
          
          if (res.success) {
            this.$message.success('外派结果提交成功')
            this.showExternalResultDialog = false
            this.externalResultForm = {
              result: ''
            }
            // 提交成功后跳转回待我处理页面
            this.$router.push({
              path: '/work-orders',
              query: { filter: 'pending_approvals' }
            })
          } else {
            this.$message.error(res.message || '提交外派结果失败')
          }
        } catch (error) {
          // 如果后端返回了错误信息，显示后端错误信息
          if (error.response && error.response.data && error.response.data.message) {
            this.$message.error(error.response.data.message)
          } else {
            this.$message.error('提交外派结果失败')
          }
        } finally {
          this.externalResultSubmitting = false
        }
      })
    },
    async searchStaff(query) {
      if (!query) {
        this.staffList = []
        return
      }
      this.staffSearchLoading = true
      try {
        const res = await searchStaff({ keyword: query })
        if (res.success) {
          this.staffList = res.data || []
        }
      } catch (error) {
        // 忽略错误
      } finally {
        this.staffSearchLoading = false
      }
    },
    getStatusType(status) {
      const map = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'returned': 'info',
        'completed': 'success',
        'terminated': 'info',
        'external': 'warning'
      }
      return map[status] || ''
    },
    getStatusText(status) {
      const map = {
        'pending': '待审批',
        'approved': '已批准',
        'rejected': '已拒绝',
        'returned': '已打回',
        'completed': '已完成',
        'terminated': '已终止',
        'external': '外派'
      }
      return map[status] || status
    },
    getFlowActionText(action) {
      const map = {
        'create': '创建工单',
        'assign': '分配',
        'approve': '已完成',
        'reject': '拒绝',
        'return': '打回',
        'return_to_applicant': '打回给申请人',
        'transfer': '转派',
        'terminate': '终止',
        'complete': '完成',
        'external': '外派',
        'cancel': '撤销',
        'draft': '保存草稿',
        'submit_draft': '提交草稿'
      }
      return map[action] || action
    },
    async handleEdit() {
      // 跳转到编辑页面（使用创建页面，但传入工单ID）
      this.$router.push({
        path: '/work-orders/create',
        query: { id: this.order.id }
      })
    },
    async handleSubmit() {
      try {
        const res = await submitDraftWorkOrder(this.order.id, {})
        if (res.success) {
          this.$message.success('工单提交成功')
          // 跳转到待我处理页面
          this.$router.push({
            path: '/work-orders',
            query: { filter: 'pending_approvals' }
          })
        }
      } catch (error) {
        this.$message.error('提交失败：' + (error.response?.data?.message || '未知错误'))
      }
    },
    async handleCancel() {
      this.$confirm('确定要撤销此工单吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          const res = await cancelWorkOrder(this.order.id)
          if (res.success) {
            this.$message.success('工单已撤销')
            // 根据来源页面跳转：如果是从工单管理页面进入的，跳回工单管理；否则跳转到待我处理页面
            if (this.isFromManagement) {
              this.$router.push({
                path: '/work-orders/management'
              })
            } else {
              // 跳转到待我处理页面
              this.$router.push({
                path: '/work-orders',
                query: { filter: 'pending_approvals' }
              })
            }
          }
        } catch (error) {
          this.$message.error('撤销失败：' + (error.response?.data?.message || '未知错误'))
        }
      }).catch(() => {})
    }
  }
}
</script>

<style lang="scss" scoped>
.work-order-detail {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
    }
  }
}
</style>

