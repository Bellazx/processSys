<template>
  <div class="form-config-detail">
    <el-card>
      <div slot="header" class="card-header">
        <span>表单配置详情</span>
        <div>
          <el-button @click="goBack">返回</el-button>
          <el-button 
            type="primary" 
            @click="saveConfig" 
            :loading="saving"
            :disabled="config.status === 'published'"
          >
            保存
          </el-button>
          <el-button 
            v-if="config.status === 'draft'" 
            type="success" 
            @click="publishConfig"
            :disabled="!canPublish"
          >
            发布
          </el-button>
          <el-button 
            v-if="config.status === 'published'" 
            type="warning" 
            @click="archiveConfig"
          >
            下架
          </el-button>
        </div>
      </div>

      <el-form :model="config" label-width="120px" ref="configForm">
        <el-form-item label="工单类别">
          <div v-if="config.category_name" style="display: flex; align-items: center;">
            <span style="font-size: 16px; font-weight: 500; margin-right: 10px;">{{ config.category_name }}</span>
            <span style="color: #909399; font-size: 14px;">({{ config.category_code }})</span>
          </div>
          <el-select 
            v-else
            v-model="config.category_id" 
            :disabled="config.id !== null" 
            style="width: 300px"
            placeholder="请选择工单类别"
          >
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.category_name"
              :value="cat.id"
            >
              <span>{{ cat.category_name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px;">({{ cat.category_code }})</span>
            </el-option>
          </el-select>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            表单名称自动使用类别名称，无需单独配置
          </div>
        </el-form-item>
        <el-form-item v-if="config.id" label="状态">
          <el-tag :type="getStatusType(config.status)">
            {{ getStatusText(config.status) }}
          </el-tag>
        </el-form-item>
      </el-form>

      <div class="fields-section">
        <div class="section-header">
          <h3>表单字段配置</h3>
          <el-button 
            type="primary" 
            size="small" 
            @click="addField"
            :disabled="config.status === 'published'"
          >
            添加字段
          </el-button>
        </div>
        
        <!-- 已发布状态提示 -->
        <el-alert
          v-if="config.status === 'published'"
          title="表单已发布"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <div slot="description">
            <p style="margin: 5px 0;">已发布的表单配置不能修改，请先点击"下架"按钮将表单转为草稿状态后再进行编辑。</p>
          </div>
        </el-alert>
        
        <!-- 系统自动字段说明 -->
        <el-alert
          title="系统自动字段"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <div slot="description">
            <p style="margin: 5px 0;">以下字段由系统自动填充，无需配置：</p>
            <ul style="margin: 5px 0; padding-left: 20px;">
              <li>申请人姓名</li>
              <li>申请人学工号</li>
              <li>申请人部门</li>
              <li>申请日期</li>
              <li>申请人手机号</li>
              <li>申请人邮箱</li>
              <li>身份类型</li>
            </ul>
            <p style="margin: 5px 0; color: #909399; font-size: 12px;">这些字段会在工单创建时自动显示，用户无需填写。</p>
          </div>
        </el-alert>

        <el-table 
          :data="allFields" 
          border 
          style="margin-top: 20px"
          :row-key="getRowKey"
        >
          <el-table-column type="index" label="序号" width="60"></el-table-column>
          <el-table-column prop="field_label" label="字段标签" width="150">
            <template slot-scope="scope">
              <el-input
                v-if="!scope.row.is_system"
                v-model="scope.row.field_label"
                size="small"
                :disabled="config.status === 'published'"
                @blur="updateField(scope.$index)"
              ></el-input>
              <span v-else style="color: #409EFF;">
                {{ scope.row.field_label }}
                <el-tag size="mini" type="info" style="margin-left: 5px;">系统</el-tag>
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="field_key" label="字段标识" width="150">
            <template slot-scope="scope">
              <el-input
                v-if="!scope.row.is_system"
                v-model="scope.row.field_key"
                size="small"
                :disabled="scope.row.id || config.status === 'published'"
                @blur="updateField(scope.$index)"
              ></el-input>
              <span v-else style="color: #909399;">{{ scope.row.field_key }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="field_type" label="字段类型" width="150">
            <template slot-scope="scope">
              <el-select
                v-if="!scope.row.is_system"
                v-model="scope.row.field_type"
                size="small"
                :disabled="config.status === 'published'"
                @change="updateField(scope.$index)"
              >
                <el-option label="单行文本" value="text"></el-option>
                <el-option label="数字" value="number"></el-option>
                <el-option label="多行文本" value="textarea"></el-option>
                <el-option label="图片" value="image"></el-option>
                <el-option label="文件" value="file"></el-option>
                <el-option label="下拉选择" value="select"></el-option>
                <el-option label="单选" value="radio"></el-option>
                <el-option label="多选" value="checkbox"></el-option>
                <el-option label="日期" value="date"></el-option>
                <el-option label="日期时间" value="datetime"></el-option>
              </el-select>
              <span v-else style="color: #909399;">{{ getFieldTypeLabel(scope.row.field_type) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="字段选项" min-width="200">
            <template slot-scope="scope">
              <el-input
                v-if="!scope.row.is_system && ['select', 'radio', 'checkbox'].includes(scope.row.field_type)"
                v-model="scope.row.field_options_text"
                size="small"
                placeholder="每行一个选项"
                type="textarea"
                :rows="2"
                :disabled="config.status === 'published'"
                @blur="updateFieldOptions(scope.$index)"
              ></el-input>
              <span v-else style="color: #999">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_required" label="必填" width="80">
            <template slot-scope="scope">
              <el-switch
                v-if="!scope.row.is_system"
                v-model="scope.row.is_required"
                :disabled="config.status === 'published'"
                @change="updateField(scope.$index)"
              ></el-switch>
              <el-tag v-else size="mini" type="success">是</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="100">
            <template slot-scope="scope">
              <el-input-number
                v-model="scope.row.sort_order"
                size="small"
                :min="0"
                :disabled="config.status === 'published'"
                @change="updateSortOrder"
              ></el-input-number>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template slot-scope="scope">
              <el-button
                v-if="!scope.row.is_system"
                size="mini"
                type="danger"
                :disabled="config.status === 'published'"
                @click="removeField(scope.$index)"
              >
                删除
              </el-button>
              <span v-else style="color: #909399; font-size: 12px;">系统字段</span>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="allFields.length === 0" style="text-align: center; padding: 40px; color: #999">
          暂无字段，请添加字段
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { getFormConfig, updateFormConfig, publishFormConfig, createFormConfig, archiveFormConfig } from '@/api/formConfig'
import { getCategories } from '@/api/admin'

export default {
  name: 'FormConfigDetail',
  data() {
    return {
      config: {
        id: null,
        category_id: null,
        name: '',
        status: 'draft',
        fields_config: [],
        system_fields_order: {}
      },
      fields: [],
      categories: [],
      saving: false,
      configId: null
    }
  },
  computed: {
    canPublish() {
      return this.fields.length > 0 && this.fields.every(f => f.field_key && f.field_label)
    },
    // 获取系统自动字段定义
    getSystemFields() {
      return [
        { field_key: 'applicant_name', field_label: '申请人姓名', field_type: 'text', is_required: true, is_system: true, sort_order: 0 },
        { field_key: 'applicant_id', field_label: '申请人学工号', field_type: 'text', is_required: true, is_system: true, sort_order: 1 },
        { field_key: 'applicant_dept', field_label: '申请人部门', field_type: 'text', is_required: true, is_system: true, sort_order: 2 },
        { field_key: 'apply_date', field_label: '申请日期', field_type: 'date', is_required: true, is_system: true, sort_order: 3 },
        { field_key: 'applicant_phone', field_label: '申请人手机号', field_type: 'text', is_required: true, is_system: true, sort_order: 4 },
        { field_key: 'applicant_email', field_label: '申请人邮箱', field_type: 'text', is_required: true, is_system: true, sort_order: 5 },
        { field_key: 'user_type', field_label: '身份类型', field_type: 'text', is_required: false, is_system: true, sort_order: 6 }
      ]
    },
    // 合并系统字段和自定义字段
    allFields() {
      // 从配置中获取系统字段的排序信息（如果存在）
      const systemFieldsConfig = this.config.system_fields_order || {}
      
      // 合并系统字段和自定义字段
      const systemFields = this.getSystemFields.map(sf => {
        // 如果配置中有该字段的排序信息，使用配置的排序
        if (systemFieldsConfig[sf.field_key] !== undefined) {
          sf.sort_order = systemFieldsConfig[sf.field_key]
        }
        return { ...sf }
      })
      
      // 直接使用 fields 数组的引用，避免重新创建对象导致数据丢失
      const customFields = this.fields.map(f => {
        // 确保每个字段都有_temp_id（如果没有的话）
        if (!f._temp_id && !f.field_key) {
          f._temp_id = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        }
        // 添加 is_system 标记，但不创建新对象，保持引用
        f.is_system = false
        return f
      })
      
      // 合并并排序
      const all = [...systemFields, ...customFields]
      return all.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    }
  },
  mounted() {
    this.configId = this.$route.params.id
    this.loadCategories()
    if (this.configId && this.configId !== 'new') {
      this.loadConfig()
    } else {
      // 新建表单配置
      const categoryId = this.$route.query.category_id
      if (categoryId) {
        this.config.category_id = parseInt(categoryId)
      }
    }
  },
  methods: {
    async loadCategories() {
      try {
        const res = await getCategories({ is_active: true })
        if (res.success) {
          this.categories = res.data
        }
      } catch (error) {
        this.$message.error('加载工单类别失败')
      }
    },
    async loadConfig() {
      try {
        const res = await getFormConfig(this.configId)
        if (res.success) {
          this.config = res.data
          // 确保类别名称和代码已加载
          if (res.data.category_name) {
            this.config.category_name = res.data.category_name
          }
          if (res.data.category_code) {
            this.config.category_code = res.data.category_code
          }
          // 加载系统字段排序配置（如果存在）
          if (res.data.system_fields_order) {
            this.config.system_fields_order = res.data.system_fields_order
          } else {
            this.config.system_fields_order = {}
          }
          
          this.fields = res.data.fields_config || []
          // 处理字段选项（将JSON转换为文本）
          this.fields.forEach(field => {
            if (field.field_options && typeof field.field_options === 'string') {
              try {
                const options = JSON.parse(field.field_options)
                field.field_options_text = Array.isArray(options) ? options.join('\n') : ''
              } catch (e) {
                field.field_options_text = ''
              }
            } else if (Array.isArray(field.field_options)) {
              field.field_options_text = field.field_options.join('\n')
            } else {
              field.field_options_text = ''
            }
          })
          // 按排序顺序排序
          this.fields.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
        }
      } catch (error) {
        this.$message.error('加载表单配置失败')
        this.goBack()
      }
    },
    addField() {
      // 计算新字段的排序值：应该是所有字段（包括系统字段）中最大的 sort_order + 1
      let maxSortOrder = 0
      
      // 检查系统字段的最大排序值
      if (this.getSystemFields.length > 0) {
        const systemMaxSort = Math.max(...this.getSystemFields.map(sf => sf.sort_order || 0))
        maxSortOrder = Math.max(maxSortOrder, systemMaxSort)
      }
      
      // 检查自定义字段的最大排序值
      if (this.fields.length > 0) {
        const customMaxSort = Math.max(...this.fields.map(f => f.sort_order || 0))
        maxSortOrder = Math.max(maxSortOrder, customMaxSort)
      }
      
      // 生成唯一的临时ID（用于row-key，避免输入时重新渲染）
      const tempId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      const newField = {
        _temp_id: tempId,  // 临时唯一ID，用于row-key
        field_key: '',
        field_label: '',
        field_type: 'text',
        field_options: [],
        field_options_text: '',
        is_required: false,
        sort_order: maxSortOrder + 1  // 添加在最后
      }
      this.fields.push(newField)
    },
    getRowKey(row) {
      // 使用临时ID或field_key作为row-key
      // 系统字段使用field_key，自定义字段使用_temp_id（如果存在）或field_key
      if (row.is_system) {
        return `system_${row.field_key}`
      }
      return row._temp_id || row.field_key || `field_${row.sort_order || 0}`
    },
    updateField(index) {
      // 字段更新时自动保存到fields数组
      // 实际保存会在点击保存按钮时统一保存
    },
    updateFieldOptions(index) {
      // index 是 allFields 的索引，需要找到对应的字段
      const field = this.allFields[index]
      if (!field || field.is_system) {
        return
      }
      // 找到在 fields 数组中的实际索引
      const actualIndex = this.fields.findIndex(f => {
        if (field._temp_id) {
          return f._temp_id === field._temp_id
        }
        return f.field_key === field.field_key
      })
      if (actualIndex === -1) {
        return
      }
      const actualField = this.fields[actualIndex]
      if (actualField && actualField.field_options_text !== undefined) {
        // 将文本转换为数组
        if (actualField.field_options_text) {
          const options = actualField.field_options_text.split('\n').filter(opt => opt.trim())
          actualField.field_options = options
        } else {
          actualField.field_options = []
        }
      }
    },
    removeField(index) {
      this.$confirm('确定要删除该字段吗？', '提示', {
        type: 'warning'
      }).then(() => {
        // 找到实际在fields数组中的索引
        const field = this.allFields[index]
        if (field && !field.is_system) {
          const actualIndex = this.fields.findIndex(f => f.field_key === field.field_key)
          if (actualIndex !== -1) {
            this.fields.splice(actualIndex, 1)
            // 重新排序自定义字段
            this.fields.forEach((f, idx) => {
              f.sort_order = idx + this.getSystemFields.length
            })
          }
        }
      })
    },
    updateSortOrder() {
      // 排序顺序更新时，自动重新排序
      // 这里不需要额外操作，computed属性会自动处理
    },
    getFieldTypeLabel(type) {
      const map = {
        'text': '单行文本',
        'number': '数字',
        'textarea': '多行文本',
        'image': '图片',
        'file': '文件',
        'select': '下拉选择',
        'radio': '单选',
        'checkbox': '多选',
        'date': '日期',
        'datetime': '日期时间'
      }
      return map[type] || type
    },
    async saveConfig() {
      // 验证必填项
      if (!this.config.category_id) {
        this.$message.warning('请选择工单类别')
        return
      }
      // 系统保留字段列表
      const reservedFields = [
        'applicant_name', 'applicant_id', 'applicant_code', 'applicant_dept',
        'apply_date', 'applicant_phone', 'applicant_email', 'user_type'
      ]
      
      // 验证字段（只验证自定义字段，排除系统字段和空字段）
      const validFields = this.fields.filter(f => f.field_key && f.field_label && !f.is_system)
      
      // 至少要有有效的自定义字段（系统字段总是存在的）
      if (validFields.length === 0) {
        this.$message.warning('请至少添加一个有效的自定义字段（标识和标签不能为空）')
        return
      }
      
      if (validFields.length === 0) {
        this.$message.warning('请至少添加一个有效的自定义字段（标识和标签不能为空）')
        return
      }
      
      for (let i = 0; i < validFields.length; i++) {
        const field = validFields[i]
        
        // 检查是否为系统保留字段
        if (reservedFields.includes(field.field_key.toLowerCase())) {
          this.$message.warning(`第${i + 1}个字段的标识"${field.field_key}"是系统保留字段，不能使用。系统会自动显示这些字段。`)
          return
        }
        
        // 验证字段标识格式（只能包含字母、数字、下划线）
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(field.field_key)) {
          this.$message.warning(`第${i + 1}个字段的标识格式不正确（只能包含字母、数字、下划线，且不能以数字开头）`)
          return
        }
      }
      // 检查字段标识是否重复（只检查有效字段）
      const keys = validFields.map(f => f.field_key)
      if (new Set(keys).size !== keys.length) {
        this.$message.warning('字段标识不能重复')
        return
      }

      this.saving = true
      try {
        // 构建字段配置（只保存有效字段）
        const fieldsConfig = validFields.map(field => {
          const config = {
            field_key: field.field_key,
            field_label: field.field_label,
            field_type: field.field_type,
            is_required: field.is_required,
            sort_order: field.sort_order || 0
          }
          // 如果是选择类型，添加选项
          if (['select', 'radio', 'checkbox'].includes(field.field_type)) {
            if (field.field_options && field.field_options.length > 0) {
              config.field_options = field.field_options
            } else if (field.field_options_text) {
              config.field_options = field.field_options_text.split('\n').filter(opt => opt.trim())
            }
          }
          return config
        })

        // 提取系统字段的排序信息
        const systemFieldsOrder = {}
        this.getSystemFields.forEach(sf => {
          const fieldInList = this.allFields.find(f => f.field_key === sf.field_key && f.is_system)
          if (fieldInList) {
            systemFieldsOrder[sf.field_key] = fieldInList.sort_order
          }
        })
        
        const data = {
          category_id: this.config.category_id,
          fields_config: fieldsConfig,
          system_fields_order: systemFieldsOrder
        }

        let res
        if (this.configId && this.configId !== 'new') {
          res = await updateFormConfig(this.configId, data)
        } else {
          res = await createFormConfig(data)
          if (res.success && res.data && res.data.id) {
            this.configId = res.data.id
            this.config.id = res.data.id
            this.$router.replace(`/form-configs/${this.configId}`)
          }
        }

        if (res.success) {
          this.$message.success('保存成功')
          // 如果是新建，重新加载配置
          if (this.configId && this.configId !== 'new' && !this.config.id) {
            this.loadConfig()
          }
        }
      } catch (error) {
        this.$message.error('保存失败')
      } finally {
        this.saving = false
      }
    },
    async publishConfig() {
      if (!this.canPublish) {
        this.$message.warning('请先完善表单字段配置')
        return
      }
      // 先保存
      await this.saveConfig()
      if (!this.configId || this.configId === 'new') {
        return
      }
      try {
        const res = await publishFormConfig(this.configId)
        if (res.success) {
          this.$message.success('发布成功')
          this.loadConfig()
        }
      } catch (error) {
        this.$message.error('发布失败')
      }
    },
    async archiveConfig() {
      this.$confirm('确定要下架该表单配置吗？下架后表单将转为草稿状态，可以重新编辑。', '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await archiveFormConfig(this.configId)
          if (res.success) {
            this.$message.success('下架成功，表单已转为草稿状态')
            this.loadConfig()
          } else {
            this.$message.error(res.message || '下架失败')
          }
        } catch (error) {
          this.$message.error('下架失败')
        }
      }).catch(() => {
        // 用户取消
      })
    },
    goBack() {
      this.$router.push('/dashboard/form-configs')
    },
    getStatusType(status) {
      const map = {
        'draft': 'info',
        'published': 'success',
        'archived': 'warning'
      }
      return map[status] || ''
    },
    getStatusText(status) {
      const map = {
        'draft': '草稿',
        'published': '已发布',
        'archived': '已归档'
      }
      return map[status] || status
    }
  }
}
</script>

<style lang="scss" scoped>
.form-config-detail {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .fields-section {
    margin-top: 30px;

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      h3 {
        margin: 0;
      }
    }
  }
}
</style>
