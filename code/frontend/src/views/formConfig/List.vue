<template>
  <div class="form-config-list">
    <h2>表单配置</h2>
    <el-card>
      <div slot="header" class="card-header">
        <div>
          <el-button type="primary" @click="showCreateDialog">新增表单配置</el-button>
        </div>
      </div>
      <el-table 
        :data="configs" 
        v-loading="loading" 
        border 
        :default-sort="{prop: 'create_time', order: 'descending'}"
        :show-header="true"
        fit
      >
        <el-table-column prop="category_name" label="工单类别" width="200">
          <template slot-scope="scope">
            <div>
              <div style="font-weight: 500;">{{ scope.row.category_name }}</div>
              <div style="font-size: 12px; color: #909399;">{{ scope.row.category_code }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建人" width="120"></el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180">
          <template slot-scope="scope">
            {{ formatDate(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="250">
          <template slot-scope="scope">
            <el-button size="mini" @click="edit(scope.row.id)">编辑</el-button>
            <el-button 
              v-if="scope.row.status === 'draft'"
              size="mini" 
              type="success"
              @click="publish(scope.row.id)"
            >
              发布
            </el-button>
            <el-button 
              v-if="scope.row.status === 'published'"
              size="mini" 
              type="warning"
              @click="archive(scope.row.id)"
            >
              下架
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增表单配置对话框 -->
    <el-dialog
      title="新增表单配置"
      :visible.sync="createDialogVisible"
      width="500px"
      @close="resetCreateForm"
    >
      <el-form :model="createForm" :rules="createRules" ref="createForm" label-width="100px">
        <el-form-item label="工单类别" prop="category_id">
          <el-select 
            v-model="createForm.category_id" 
            placeholder="请选择工单类别"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="cat in availableCategories"
              :key="cat.id"
              :label="cat.category_name"
              :value="cat.id"
            >
              <span>{{ cat.category_name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px;">({{ cat.category_code }})</span>
            </el-option>
          </el-select>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            表单名称将自动使用类别名称
          </div>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createConfig">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getFormConfigs, publishFormConfig, archiveFormConfig, createFormConfig } from '@/api/formConfig'
import { getCategories } from '@/api/admin'

export default {
  name: 'FormConfigList',
  data() {
    return {
      configs: [],
      loading: false,
      categories: [],
      createDialogVisible: false,
      createForm: {
        category_id: null
      },
      createRules: {
        category_id: [{ required: true, message: '请选择工单类别', trigger: 'change' }]
      }
    }
  },
  mounted() {
    this.loadConfigs()
    this.loadCategories()
  },
  computed: {
    // 获取还没有表单配置的类别
    availableCategories() {
      const configuredCategoryIds = this.configs.map(c => c.category_id)
      return this.categories.filter(cat => !configuredCategoryIds.includes(cat.id))
    }
  },
  methods: {
    async loadConfigs() {
      this.loading = true
      try {
        const res = await getFormConfigs()
        if (res.success) {
          this.configs = res.data
        }
      } catch (error) {
        this.$message.error('加载表单配置失败')
      } finally {
        this.loading = false
      }
    },
    async loadCategories() {
      try {
        const res = await getCategories({ is_active: true })
        if (res.success) {
          this.categories = res.data
        }
      } catch (error) {
        // 忽略错误
      }
    },
    showCreateDialog() {
      // 打开对话框前刷新类别列表，确保显示最新类别
      this.loadCategories()
      this.createDialogVisible = true
    },
    resetCreateForm() {
      this.createForm = {
        category_id: null
      }
      this.$refs.createForm && this.$refs.createForm.resetFields()
    },
    async createConfig() {
      this.$refs.createForm.validate(async (valid) => {
        if (!valid) return
        
        // 先尝试创建，如果已存在则跳转到编辑页面
        try {
          const res = await createFormConfig({
            category_id: this.createForm.category_id
          })
          
          if (res.success) {
            // 创建成功，跳转到编辑页面
            this.$message.success('表单配置创建成功')
            this.createDialogVisible = false
            this.loadConfigs() // 刷新列表
            this.$router.push(`/dashboard/form-configs/${res.data.id}`)
          }
        } catch (error) {
          // 如果返回400且是已存在的情况，跳转到编辑页面
          if (error.response && error.response.status === 400) {
            const data = error.response.data
            if (data && data.data && data.data.existing && data.data.id) {
              this.$message.info('该类别已有表单配置，将跳转到编辑页面')
              this.createDialogVisible = false
              this.loadConfigs() // 刷新列表
              this.$router.push(`/dashboard/form-configs/${data.data.id}`)
            } else {
              this.$message.error(data.message || '创建失败')
            }
          } else {
            this.$message.error('创建失败')
          }
        }
      })
    },
    edit(id) {
      this.$router.push(`/dashboard/form-configs/${id}`)
    },
    async publish(id) {
      try {
        const res = await publishFormConfig(id)
        if (res.success) {
          this.$message.success('发布成功')
          this.loadConfigs()
        } else {
          this.$message.error(res.message || '发布失败')
        }
      } catch (error) {
        this.$message.error('发布失败')
      }
    },
    async archive(id) {
      this.$confirm('确定要下架该表单配置吗？下架后表单将转为草稿状态，可以重新编辑。', '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await archiveFormConfig(id)
          if (res.success) {
            this.$message.success('下架成功，表单已转为草稿状态')
            this.loadConfigs()
          } else {
            this.$message.error(res.message || '下架失败')
          }
        } catch (error) {
          this.$message.error('下架失败')
        }
      })
    },
    getStatusType(status) {
      const map = {
        'draft': 'info',
        'published': 'success'
      }
      return map[status] || ''
    },
    getStatusText(status) {
      const map = {
        'draft': '草稿',
        'published': '已发布'
      }
      return map[status] || status
    },
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

