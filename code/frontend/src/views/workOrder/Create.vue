<template>
  <div class="work-order-create">
    <h2>{{ isEditMode ? '编辑工单' : '新建工单' }}</h2>
    <el-card>
      <el-form :model="form" label-width="120px">
        <!-- 申请人基础信息（系统自动填充，只读） -->
        <el-divider content-position="left">申请人信息（系统自动填充）</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="申请人姓名">
              <el-input :value="userInfo.user_name" disabled></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请人学工号">
              <el-input :value="userInfo.user_id" disabled></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请人部门">
              <el-input :value="userInfo.user_dept" disabled></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="申请日期">
              <el-input :value="applyDate" disabled></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请人手机号">
              <el-input :value="userInfo.user_phone" disabled></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="申请人邮箱">
              <el-input :value="userInfo.user_email" disabled></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">工单信息</el-divider>
        <el-form-item label="工单类别" required>
          <el-select v-model="form.category_id" placeholder="请选择工单类别">
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.category_name"
              :value="category.id"
            ></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="分配方式" required>
          <el-radio-group v-model="form.assign_type">
            <el-radio label="individual">分配给个人</el-radio>
            <el-radio label="department">分配给部门</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item 
          v-if="form.assign_type === 'individual'" 
          label="审批人" 
          required
        >
          <el-select 
            v-model="form.approver_ids" 
            multiple 
            filterable
            remote
            :remote-method="searchStaff"
            placeholder="请选择审批人"
          >
            <el-option
              v-for="staff in staffList"
              :key="staff.code"
              :label="`${staff.name} (${staff.code})`"
              :value="staff.code"
            ></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item 
          v-if="form.assign_type === 'department'" 
          label="部门" 
          required
        >
          <el-select v-model="form.assign_to_dept" placeholder="请选择部门">
            <el-option
              v-for="dept in departments"
              :key="dept"
              :label="dept"
              :value="dept"
            ></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 动态表单字段将在这里渲染 -->
        <el-divider v-if="formFields.length > 0" content-position="left">其他信息</el-divider>
        <div v-if="formFields.length > 0">
          <el-form-item
            v-for="field in formFields"
            :key="field.field_key"
            :label="field.field_label"
            :required="field.is_required"
          >
            <!-- 文本输入 -->
            <el-input
              v-if="field.field_type === 'text'"
              v-model="formData[field.field_key]"
              :placeholder="`请输入${field.field_label}`"
            ></el-input>
            
            <!-- 数字输入 -->
            <el-input-number
              v-else-if="field.field_type === 'number'"
              v-model="formData[field.field_key]"
              :placeholder="`请输入${field.field_label}`"
              style="width: 100%"
            ></el-input-number>
            
            <!-- 多行文本 -->
            <el-input
              v-else-if="field.field_type === 'textarea'"
              v-model="formData[field.field_key]"
              type="textarea"
              :rows="4"
              :placeholder="`请输入${field.field_label}`"
            ></el-input>
            
            <!-- 下拉选择 -->
            <el-select
              v-else-if="field.field_type === 'select'"
              v-model="formData[field.field_key]"
              :placeholder="`请选择${field.field_label}`"
              style="width: 100%"
            >
              <el-option
                v-for="option in getFieldOptions(field)"
                :key="option"
                :label="option"
                :value="option"
              ></el-option>
            </el-select>
            
            <!-- 单选 -->
            <el-radio-group
              v-else-if="field.field_type === 'radio'"
              v-model="formData[field.field_key]"
            >
              <el-radio
                v-for="option in getFieldOptions(field)"
                :key="option"
                :label="option"
              >
                {{ option }}
              </el-radio>
            </el-radio-group>
            
            <!-- 多选 -->
            <el-checkbox-group
              v-else-if="field.field_type === 'checkbox'"
              v-model="formData[field.field_key]"
            >
              <el-checkbox
                v-for="option in getFieldOptions(field)"
                :key="option"
                :label="option"
              >
                {{ option }}
              </el-checkbox>
            </el-checkbox-group>
            
            <!-- 日期 -->
            <el-date-picker
              v-else-if="field.field_type === 'date'"
              v-model="formData[field.field_key]"
              type="date"
              :placeholder="`请选择${field.field_label}`"
              style="width: 100%"
              value-format="yyyy-MM-dd"
            ></el-date-picker>
            
            <!-- 日期时间 -->
            <el-date-picker
              v-else-if="field.field_type === 'datetime'"
              v-model="formData[field.field_key]"
              type="datetime"
              :placeholder="`请选择${field.field_label}`"
              style="width: 100%"
              value-format="yyyy-MM-dd HH:mm:ss"
            ></el-date-picker>
            
            <!-- 图片上传 -->
            <div v-else-if="field.field_type === 'image'">
              <el-upload
                :action="uploadImageUrl"
                :headers="uploadHeaders"
                :on-success="(res, file) => handleImageUploadSuccess(field.field_key, res, file)"
                :on-remove="(file, fileList) => handleImageRemove(field.field_key, file, fileList)"
                :on-exceed="() => handleImageExceed(field.field_label)"
                :file-list="getImageFileList(field.field_key)"
                list-type="picture-card"
                :limit="4"
                accept="image/*"
              >
                <i class="el-icon-plus"></i>
              </el-upload>
              <div style="margin-top: 10px; color: #909399; font-size: 12px;">
                <i class="el-icon-info"></i> 最多可上传4张图片，支持 JPG、PNG 等格式
              </div>
            </div>
            
            <!-- 文件上传 -->
            <el-upload
              v-else-if="field.field_type === 'file'"
              :action="uploadFileUrl"
              :headers="uploadHeaders"
              :on-success="(res, file) => handleFileUploadSuccess(field.field_key, res, file)"
              :on-remove="() => handleFileRemove(field.field_key)"
              :on-exceed="() => handleFileExceed(field.field_label)"
              :file-list="getFileList(field.field_key)"
              :limit="1"
            >
              <el-button size="small" type="primary">点击上传</el-button>
              <div slot="tip" class="el-upload__tip">
                <i class="el-icon-info"></i> 最多只能上传1个文件，如需更换请先删除当前文件
              </div>
            </el-upload>
            
            <!-- 默认文本输入 -->
            <el-input
              v-else
              v-model="formData[field.field_key]"
              :placeholder="`请输入${field.field_label}`"
            ></el-input>
          </el-form-item>
        </div>
        
        <el-form-item>
          <el-button 
            v-if="isEditMode"
            @click="saveOnly"
            :loading="submitting"
            :disabled="!canSave"
          >
            保存
          </el-button>
          <el-button 
            type="primary" 
            @click="submit" 
            :loading="submitting"
            :disabled="!canSubmit"
          >
            {{ isEditMode ? '保存并提交' : '提交' }}
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { createWorkOrder, getWorkOrderDetail, updateWorkOrder, submitDraftWorkOrder } from '@/api/workOrder'
import { getCategories, searchStaff, getDepartments } from '@/api/admin'
import { getFormConfigs } from '@/api/formConfig'
import { mapState } from 'vuex'
import request from '@/utils/request'

export default {
  name: 'CreateWorkOrder',
  data() {
    return {
      form: {
        category_id: null,
        assign_type: 'individual',
        approver_ids: [],
        assign_to_dept: null
      },
      formData: {},
      categories: [],
      staffList: [],
      departments: [],
      formFields: [],
      submitting: false,
      // 文件上传配置
      uploadImageUrl: '/process/upload/image',
      uploadFileUrl: '/process/upload/file',
      orderId: null,  // 编辑模式下的工单ID
      isEditMode: false  // 是否是编辑模式
    }
  },
  computed: {
    ...mapState('user', ['user_id', 'user_dept', 'user_name', 'user_phone', 'user_email']),
    userInfo() {
      return {
        user_id: this.user_id,
        user_name: this.user_name,
        user_dept: this.user_dept,
        user_phone: this.user_phone,
        user_email: this.user_email
      }
    },
    applyDate() {
      const now = new Date()
      return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
    },
    uploadHeaders() {
      // 上传请求头（如果需要认证）
      return {}
    },
    canSave() {
      // 检查是否可以保存（编辑模式下只需要有类别即可）
      if (this.isEditMode) {
        return !!this.form.category_id
      }
      return false
    },
    canSubmit() {
      // 检查是否可以提交
      // 1. 工单类别必须选择
      if (!this.form.category_id) {
        return false
      }
      
      // 2. 分配方式必须选择（虽然有默认值，但确保已设置）
      if (!this.form.assign_type) {
        return false
      }
      
      // 3. 如果分配方式为"分配给个人"，审批人必须至少选择一个
      if (this.form.assign_type === 'individual') {
        if (!this.form.approver_ids || this.form.approver_ids.length === 0) {
          return false
        }
      }
      
      // 4. 如果分配方式为"分配给部门"，部门必须选择
      if (this.form.assign_type === 'department') {
        if (!this.form.assign_to_dept) {
          return false
        }
      }
      
      return true
    }
  },
  mounted() {
    this.loadCategories()
    this.loadDepartments()
    const categoryId = this.$route.query.category_id
    const orderId = this.$route.query.id
    if (orderId) {
      // 编辑模式
      this.orderId = parseInt(orderId)
      this.isEditMode = true
      this.loadOrderDetail()
    } else if (categoryId) {
      // 新建模式，但指定了类别
      this.form.category_id = parseInt(categoryId)
      this.loadFormConfig()
    }
  },
  watch: {
    'form.category_id'() {
      this.loadFormConfig()
    }
  },
  methods: {
    async loadCategories() {
      try {
        // 1. 先获取所有已发布的表单配置
        const formConfigRes = await getFormConfigs({ status: 'published' })
        if (!formConfigRes.success) {
          this.categories = []
          return
        }
        
        // 2. 提取已发布表单配置的类别ID
        const publishedCategoryIds = formConfigRes.data.map(config => config.category_id)
        
        if (publishedCategoryIds.length === 0) {
          this.categories = []
          return
        }
        
        // 3. 获取所有激活的类别
        const categoriesRes = await getCategories({ is_active: true })
        if (categoriesRes.success) {
          // 4. 只保留那些有已发布表单配置的类别
          this.categories = categoriesRes.data.filter(cat => 
            publishedCategoryIds.includes(cat.id)
          )
        }
      } catch (error) {
        this.$message.error('加载类别失败')
        this.categories = []
      }
    },
    async loadDepartments() {
      try {
        const res = await getDepartments()
        if (res.success) {
          this.departments = res.data || []
        }
      } catch (error) {
        this.$message.error('加载部门列表失败')
      }
    },
    async loadFormConfig() {
      if (!this.form.category_id) return
      
      try {
        const res = await getFormConfigs({ 
          category_id: this.form.category_id,
          status: 'published'
        })
        if (res.success && res.data.length > 0) {
          const config = res.data[0]
          this.formFields = config.fields_config || []
          // 如果是编辑模式，确保form_config_id被设置（虽然可能不需要，但为了完整性）
          if (this.isEditMode && config.id) {
            // form_config_id会在提交时使用
          }
        }
      } catch (error) {
        this.$message.error('加载表单配置失败')
      }
    },
    async searchStaff(query) {
      if (!query) return
      try {
        const res = await searchStaff({ keyword: query })
        if (res.success) {
          this.staffList = res.data
        }
      } catch (error) {
        // 忽略错误
      }
    },
    getFieldOptions(field) {
      // 获取字段选项列表
      if (field.field_options) {
        if (Array.isArray(field.field_options)) {
          return field.field_options
        }
        if (typeof field.field_options === 'string') {
          try {
            const parsed = JSON.parse(field.field_options)
            return Array.isArray(parsed) ? parsed : []
          } catch {
            return field.field_options.split('\n').filter(opt => opt.trim())
          }
        }
      }
      return []
    },
    getImageFileList(fieldKey) {
      // 获取图片文件列表（支持多张图片）
      const value = this.formData[fieldKey]
      if (!value) {
        return []
      }
      
      // 如果是数组，返回多张图片
      if (Array.isArray(value)) {
        return value.map((url, index) => {
          // 使用稳定的uid，基于fieldKey和URL生成，避免位置跳动
          const stableUid = `${fieldKey}_${index}_${url.replace(/[^a-zA-Z0-9]/g, '_')}`
          return {
            name: url.split('/').pop() || `image_${index + 1}`,
            url: url,
            uid: stableUid
          }
        })
      }
      
      // 如果是字符串（兼容旧数据），转换为数组格式
      if (typeof value === 'string' && value) {
        const stableUid = `${fieldKey}_0_${value.replace(/[^a-zA-Z0-9]/g, '_')}`
        return [{
          name: value.split('/').pop() || 'image',
          url: value,
          uid: stableUid
        }]
      }
      
      return []
    },
    getFileList(fieldKey) {
      // 获取文件列表
      const fileInfo = this.formData[fieldKey]
      if (fileInfo) {
        if (typeof fileInfo === 'string') {
          return [{
            name: fileInfo.split('/').pop() || 'file',
            url: fileInfo
          }]
        }
        if (fileInfo && typeof fileInfo === 'object' && fileInfo.name && fileInfo.url) {
          return [{
            name: fileInfo.name,
            url: fileInfo.url
          }]
        }
      }
      return []
    },
    handleImageUploadSuccess(fieldKey, response, file) {
      // 图片上传成功（支持多张图片）
      console.log('图片上传成功:', { response, file })
      let imageUrl = null
      
      // 处理不同的响应格式
      if (response) {
        if (response.success && response.data) {
          imageUrl = response.data.url || response.data
        } else if (response.url) {
          imageUrl = response.url
        } else if (typeof response === 'string') {
          imageUrl = response
        }
      }
      
      // 如果 response 中没有，尝试从 file.response 获取
      if (!imageUrl && file && file.response) {
        if (file.response.success && file.response.data) {
          imageUrl = file.response.data.url || file.response.data
        } else if (file.response.url) {
          imageUrl = file.response.url
        } else if (typeof file.response === 'string') {
          imageUrl = file.response
        }
      }
      
      if (imageUrl) {
        // 获取当前图片数组
        const currentValue = this.formData[fieldKey]
        let imageArray = []
        
        // 如果已有值，转换为数组
        if (currentValue) {
          if (Array.isArray(currentValue)) {
            imageArray = [...currentValue]
          } else if (typeof currentValue === 'string') {
            imageArray = [currentValue]
          }
        }
        
        // 检查是否超过限制
        if (imageArray.length >= 4) {
          this.$message.warning('最多只能上传4张图片')
          return
        }
        
        // 添加新图片
        imageArray.push(imageUrl)
        this.$set(this.formData, fieldKey, imageArray)
        this.$message.success('图片上传成功')
      } else {
        this.$message.error('图片上传失败：无法获取图片地址')
        console.error('无法解析上传响应:', { response, file })
      }
    },
    handleImageRemove(fieldKey, file, fileList) {
      // 删除图片（支持多张图片）
      const currentValue = this.formData[fieldKey]
      
      if (!currentValue) {
        return
      }
      
      // 如果是数组，删除对应的图片
      if (Array.isArray(currentValue)) {
        // 从 fileList 中获取剩余的图片URL
        const remainingUrls = fileList.map(f => f.url).filter(url => url)
        this.$set(this.formData, fieldKey, remainingUrls.length > 0 ? remainingUrls : null)
      } else if (typeof currentValue === 'string') {
        // 如果是字符串（兼容旧数据），清空
        this.$set(this.formData, fieldKey, null)
      }
    },
    handleFileUploadSuccess(fieldKey, response, file) {
      // 文件上传成功
      console.log('文件上传成功:', { response, file })
      let fileInfo = null
      
      // 处理不同的响应格式
      if (response) {
        if (response.success && response.data) {
          fileInfo = {
            name: response.data.name || file.name,
            url: response.data.url || response.data
          }
        } else if (response.url) {
          fileInfo = {
            name: file.name,
            url: response.url
          }
        } else if (typeof response === 'string') {
          fileInfo = {
            name: file.name,
            url: response
          }
        }
      }
      
      // 如果 response 中没有，尝试从 file.response 获取
      if (!fileInfo && file && file.response) {
        if (file.response.success && file.response.data) {
          fileInfo = {
            name: file.response.data.name || file.name,
            url: file.response.data.url || file.response.data
          }
        } else if (file.response.url) {
          fileInfo = {
            name: file.name,
            url: file.response.url
          }
        } else if (typeof file.response === 'string') {
          fileInfo = {
            name: file.name,
            url: file.response
          }
        }
      }
      
      if (fileInfo) {
        this.$set(this.formData, fieldKey, fileInfo)
        this.$message.success('文件上传成功')
      } else {
        this.$message.error('文件上传失败：无法获取文件信息')
        console.error('无法解析上传响应:', { response, file })
      }
    },
    handleFileRemove(fieldKey) {
      // 删除文件
      this.$set(this.formData, fieldKey, null)
    },
    handleImageExceed(fieldLabel) {
      // 图片上传数量超过限制
      this.$message.warning(`${fieldLabel}最多只能上传4张图片，请先删除部分图片后再上传`)
    },
    handleFileExceed(fieldLabel) {
      // 文件上传数量超过限制
      this.$message.warning(`${fieldLabel}最多只能上传1个文件，请先删除当前文件后再上传`)
    },
    async loadOrderDetail() {
      // 加载工单详情用于编辑
      try {
        const res = await getWorkOrderDetail(this.orderId)
        if (res.success) {
          const order = res.data.order
          
          // 填充基本表单数据
          this.form.category_id = order.category_id
          this.form.assign_type = order.assign_type || 'individual'
          this.form.assign_to_dept = order.assign_to_dept
          
          // 加载表单配置（必须等待配置加载完成后再填充表单数据）
          if (order.form_config_id || order.form_config) {
            // 如果有form_config_id，使用它加载配置
            if (order.form_config_id) {
              await this.loadFormConfig()
            } else if (order.form_config) {
              // 如果后端直接返回了form_config，直接使用
              this.formFields = order.form_config.fields_config || []
            }
          }
          
          // 填充表单字段数据（必须在表单配置加载后）
          if (order.form_data) {
            try {
              const parsedData = typeof order.form_data === 'string' 
                ? JSON.parse(order.form_data) 
                : order.form_data
              // 深度复制，避免响应式问题
              this.formData = JSON.parse(JSON.stringify(parsedData))
            } catch (e) {
              console.error('解析表单数据失败:', e)
              this.formData = {}
            }
          }
          
          // 如果是分配给个人，需要加载审批人信息
          if (this.form.assign_type === 'individual') {
            // 从流转记录中获取审批人ID（查找pending状态的flow记录）
            const pendingFlows = res.data.flows.filter(flow => flow.to_status === 'pending')
            if (pendingFlows.length > 0) {
              const approverIds = pendingFlows.map(flow => flow.approver_id).filter(id => id)
              this.form.approver_ids = approverIds
            } else if (order.current_approver_id) {
              // 如果没有pending的flow，尝试从current_approver_id获取
              const approverIds = order.current_approver_id.split(',').filter(id => id)
              this.form.approver_ids = approverIds
            } else {
              // 如果都没有，尝试从assign相关的flow记录中获取
              const assignFlows = res.data.flows.filter(flow => 
                flow.action === 'assign' || flow.action === 'transfer'
              )
              if (assignFlows.length > 0) {
                // 获取最后一条assign或transfer记录的审批人
                const lastAssignFlow = assignFlows[assignFlows.length - 1]
                if (lastAssignFlow.approver_id) {
                  this.form.approver_ids = [lastAssignFlow.approver_id]
                } else if (lastAssignFlow.transfer_to_id) {
                  this.form.approver_ids = [lastAssignFlow.transfer_to_id]
                }
              }
            }
          }
        }
      } catch (error) {
        this.$message.error('加载工单详情失败')
        this.$router.back()
      }
    },
    async saveOnly() {
      // 只保存，不提交（编辑模式）
      if (!this.form.category_id) {
        this.$message.warning('请选择工单类别')
        return
      }
      
      this.submitting = true
      try {
        // 获取form_config_id
        let form_config_id = null
        if (this.form.category_id) {
          try {
            const configRes = await getFormConfigs({ 
              category_id: this.form.category_id,
              status: 'published'
            })
            if (configRes.success && configRes.data.length > 0) {
              form_config_id = configRes.data[0].id
            }
          } catch (e) {
            console.error('获取表单配置ID失败:', e)
          }
        }
        
        const res = await updateWorkOrder(this.orderId, {
          category_id: this.form.category_id,
          form_config_id: form_config_id,
          assign_type: this.form.assign_type,
          approver_ids: this.form.approver_ids,
          assign_to_dept: this.form.assign_to_dept,
          form_data: this.formData
        })
        if (res.success) {
          this.$message.success('工单保存成功')
          // 返回工单详情页
          this.$router.push(`/work-orders/${this.orderId}`)
        }
      } catch (error) {
        this.$message.error('保存工单失败' + (error.response?.data?.message ? ': ' + error.response.data.message : ''))
      } finally {
        this.submitting = false
      }
    },
    async submit() {
      if (!this.form.category_id) {
        this.$message.warning('请选择工单类别')
        return
      }
      
      // 提交前检查审批人
      if (this.form.assign_type === 'individual' && (!this.form.approver_ids || this.form.approver_ids.length === 0)) {
        this.$message.warning('请选择审批人')
        return
      }
      if (this.form.assign_type === 'department' && !this.form.assign_to_dept) {
        this.$message.warning('请选择部门')
        return
      }
      
      this.submitting = true
      try {
        if (this.isEditMode) {
          // 编辑模式：先更新工单信息，然后提交
          // 获取form_config_id
          let form_config_id = null
          if (this.form.category_id) {
            try {
              const configRes = await getFormConfigs({ 
                category_id: this.form.category_id,
                status: 'published'
              })
              if (configRes.success && configRes.data.length > 0) {
                form_config_id = configRes.data[0].id
              }
            } catch (e) {
              console.error('获取表单配置ID失败:', e)
            }
          }
          
          // 先更新工单信息
          await updateWorkOrder(this.orderId, {
            category_id: this.form.category_id,
            form_config_id: form_config_id,
            assign_type: this.form.assign_type,
            approver_ids: this.form.approver_ids,
            assign_to_dept: this.form.assign_to_dept,
            form_data: this.formData
          })
          
          // 然后提交工单（改变状态为pending，重新分配审批人）
          const submitRes = await submitDraftWorkOrder(this.orderId, {
            assign_type: this.form.assign_type,
            approver_ids: this.form.approver_ids,
            assign_to_dept: this.form.assign_to_dept
          })
          
          if (submitRes.success) {
            this.$message.success('工单提交成功')
            // 跳转到待我处理页面
            this.$router.push({
              path: '/work-orders',
              query: { filter: 'pending_approvals' }
            })
          }
        } else {
          // 新建模式：创建工单
          const res = await createWorkOrder({
            category_id: this.form.category_id,
            assign_type: this.form.assign_type,
            approver_ids: this.form.approver_ids,
            assign_to_dept: this.form.assign_to_dept,
            form_data: this.formData
          })
          if (res.success) {
            this.$message.success('工单创建成功')
            this.$router.push('/work-orders')
          }
        }
      } catch (error) {
        const errorMsg = this.isEditMode ? '提交工单失败' : '创建工单失败'
        this.$message.error(errorMsg + (error.response?.data?.message ? ': ' + error.response.data.message : ''))
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.work-order-create {
  h2 {
    margin-bottom: 20px;
  }
}
</style>

