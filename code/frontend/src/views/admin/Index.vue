<template>
  <div class="admin-index">
    <h2>系统管理</h2>
    <el-tabs v-model="activeTab">
      <!-- 工单类别管理（仅超级管理员可见） -->
      <el-tab-pane v-if="isSuperAdmin" label="工单类别" name="categories">
        <el-card>
          <div slot="header" class="card-header">
            <span>工单类别管理</span>
            <el-button type="primary" size="small" @click="showCategoryDialog">新增类别</el-button>
          </div>
          <el-table :data="categories" v-loading="categoriesLoading" border>
            <el-table-column prop="category_code" label="类别代码" width="150"></el-table-column>
            <el-table-column prop="category_name" label="类别名称"></el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip></el-table-column>
            <el-table-column prop="sort_order" label="排序" width="80"></el-table-column>
            <el-table-column prop="is_active" label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'info'">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300">
              <template slot-scope="scope">
                <el-button size="mini" @click="editCategory(scope.row)">编辑</el-button>
                <el-button size="mini" type="success" @click="manageCategoryAdmins(scope.row)">设置管理员</el-button>
                <el-button size="mini" type="danger" @click="deleteCategory(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 系统管理员配置 -->
      <el-tab-pane label="系统管理员" name="admins">
        <el-card>
          <div slot="header" class="card-header">
            <span>系统管理员配置</span>
            <el-button type="primary" size="small" @click="showAdminDialog">新增管理员</el-button>
          </div>
          <el-table :data="admins" v-loading="adminsLoading" border>
            <el-table-column prop="user_id" label="学工号" width="150"></el-table-column>
            <el-table-column prop="user_name" label="姓名"></el-table-column>
            <el-table-column prop="is_super_admin" label="超级管理员" width="120">
              <template slot-scope="scope">
                <el-tag :type="scope.row.is_super_admin ? 'success' : 'info'">
                  {{ scope.row.is_super_admin ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="can_manage_form" label="可管理表单" width="120">
              <template slot-scope="scope">
                <el-tag :type="scope.row.can_manage_form ? 'success' : 'info'">
                  {{ scope.row.can_manage_form ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="can_manage_external" label="可外派" width="120">
              <template slot-scope="scope">
                <el-tag :type="scope.row.can_manage_external ? 'success' : 'info'">
                  {{ scope.row.can_manage_external ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template slot-scope="scope">
                <el-button size="mini" @click="editAdmin(scope.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="deleteAdmin(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 部门管理员配置 -->
      <el-tab-pane label="部门管理员" name="deptAdmins">
        <el-card>
          <div slot="header" class="card-header">
            <span>部门管理员配置</span>
            <el-button type="primary" size="small" @click="showDeptAdminDialog">新增部门管理员</el-button>
          </div>
          <el-table :data="deptAdmins" v-loading="deptAdminsLoading" border>
            <el-table-column prop="dept_name" label="部门名称"></el-table-column>
            <el-table-column prop="admin_id" label="管理员学工号" width="150"></el-table-column>
            <el-table-column prop="admin_name" label="管理员姓名"></el-table-column>
            <el-table-column label="操作" width="200">
              <template slot-scope="scope">
                <el-button size="mini" type="primary" @click="editDeptAdmin(scope.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="deleteDeptAdmin(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 工单类别对话框 -->
    <el-dialog
      :title="categoryDialogTitle"
      :visible.sync="categoryDialogVisible"
      width="600px"
      @close="resetCategoryForm"
    >
      <el-form :model="categoryForm" :rules="categoryRules" ref="categoryForm" label-width="100px">
        <el-form-item v-if="categoryForm.id" label="类别代码">
          <el-input v-model="categoryForm.category_code" disabled></el-input>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">类别代码由系统自动生成，不可修改</div>
        </el-form-item>
        <el-form-item label="类别名称" prop="category_name">
          <el-input v-model="categoryForm.category_name" placeholder="请输入类别名称，系统将自动生成类别代码"></el-input>
          <div v-if="!categoryForm.id" style="font-size: 12px; color: #909399; margin-top: 5px;">类别代码将根据类别名称自动生成</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="categoryForm.description" :rows="3"></el-input>
        </el-form-item>
        <el-form-item label="排序顺序">
          <el-input-number v-model="categoryForm.sort_order" :min="0"></el-input-number>
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="categoryForm.is_active"></el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </div>
    </el-dialog>

    <!-- 系统管理员对话框 -->
    <el-dialog
      title="系统管理员"
      :visible.sync="adminDialogVisible"
      width="600px"
      @close="resetAdminForm"
    >
      <el-form :model="adminForm" :rules="adminRules" ref="adminForm" label-width="120px">
        <el-form-item label="学工号" prop="user_id">
          <el-autocomplete
            v-model="adminForm.user_id"
            :fetch-suggestions="searchStaff"
            placeholder="输入学工号或姓名搜索"
            value-key="code"
            @select="handleStaffSelect"
            style="width: 100%"
          >
            <template slot-scope="{ item }">
              <div>{{ item.code }} - {{ item.name }}</div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="adminForm.user_name" disabled></el-input>
        </el-form-item>
        <el-form-item label="超级管理员">
          <el-switch v-model="adminForm.is_super_admin"></el-switch>
        </el-form-item>
        <el-form-item label="可管理表单">
          <el-switch v-model="adminForm.can_manage_form"></el-switch>
        </el-form-item>
        <el-form-item label="可外派工单">
          <el-switch v-model="adminForm.can_manage_external"></el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="adminDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAdmin">保存</el-button>
      </div>
    </el-dialog>

    <!-- 部门管理员对话框 -->
    <el-dialog
      :title="deptAdminDialogTitle"
      :visible.sync="deptAdminDialogVisible"
      width="800px"
      @close="resetDeptAdminForm"
    >
      <el-form :model="deptAdminForm" :rules="deptAdminRules" ref="deptAdminForm" label-width="120px">
        <el-form-item label="部门名称" prop="dept_name">
          <el-input v-model="deptAdminForm.dept_name" :disabled="deptAdminForm.id !== null"></el-input>
        </el-form-item>
        <el-form-item label="选择管理员" prop="selectedAdmins">
          <el-select
            v-model="deptAdminForm.selectedAdmins"
            multiple
            filterable
            remote
            :remote-method="searchStaffForDeptAdmin"
            placeholder="输入学工号或姓名搜索，可多选"
            value-key="code"
            style="width: 100%"
            @change="handleDeptAdminSelectChange"
          >
            <el-option
              v-for="item in deptAdminStaffSearchResults"
              :key="item.code"
              :label="`${item.code} - ${item.name}`"
              :value="item"
            >
              <span>{{ item.code }} - {{ item.name }}</span>
            </el-option>
          </el-select>
          <div style="margin-top: 10px; color: #909399; font-size: 12px;">
            已选择 {{ deptAdminForm.selectedAdmins.length }} 个管理员
          </div>
        </el-form-item>
        <el-form-item label="已选管理员" v-if="deptAdminForm.selectedAdmins.length > 0">
          <el-tag
            v-for="(admin, index) in deptAdminForm.selectedAdmins"
            :key="admin.code"
            closable
            @close="removeDeptAdminSelected(index)"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ admin.code }} - {{ admin.name }}
          </el-tag>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="deptAdminDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDeptAdmin" :disabled="deptAdminForm.selectedAdmins.length === 0">保存</el-button>
      </div>
    </el-dialog>

    <!-- 类别管理员管理对话框 -->
    <el-dialog
      title="类别管理员设置"
      :visible.sync="categoryAdminDialogVisible"
      width="800px"
    >
      <div style="margin-bottom: 20px;">
        <strong>类别：</strong>{{ currentCategory.category_name }} ({{ currentCategory.category_code }})
      </div>
      <div style="margin-bottom: 20px;">
        <el-button type="primary" size="small" @click="showCategoryAdminDialog">添加管理员</el-button>
      </div>
      <el-table :data="categoryAdmins" border>
        <el-table-column prop="admin_id" label="学工号" width="150"></el-table-column>
        <el-table-column prop="admin_name" label="姓名"></el-table-column>
        <el-table-column label="操作" width="150">
          <template slot-scope="scope">
            <el-button size="mini" type="danger" @click="deleteCategoryAdmin(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div slot="footer">
        <el-button @click="categoryAdminDialogVisible = false">关闭</el-button>
      </div>
    </el-dialog>

    <!-- 添加类别管理员对话框 -->
    <el-dialog
      title="添加类别管理员"
      :visible.sync="addCategoryAdminDialogVisible"
      width="800px"
      @close="resetCategoryAdminForm"
    >
      <el-form :model="categoryAdminForm" :rules="categoryAdminRules" ref="categoryAdminForm" label-width="120px">
        <el-form-item label="选择管理员" prop="selectedAdmins">
          <el-select
            v-model="categoryAdminForm.selectedAdmins"
            multiple
            filterable
            remote
            :remote-method="searchStaffForSelect"
            placeholder="输入学工号或姓名搜索，可多选"
            value-key="code"
            style="width: 100%"
            @change="handleCategoryAdminSelectChange"
          >
            <el-option
              v-for="item in staffSearchResults"
              :key="item.code"
              :label="`${item.code} - ${item.name}`"
              :value="item"
            >
              <span>{{ item.code }} - {{ item.name }}</span>
            </el-option>
          </el-select>
          <div style="margin-top: 10px; color: #909399; font-size: 12px;">
            已选择 {{ categoryAdminForm.selectedAdmins.length }} 个管理员
          </div>
        </el-form-item>
        <el-form-item label="已选管理员" v-if="categoryAdminForm.selectedAdmins.length > 0">
          <el-tag
            v-for="(admin, index) in categoryAdminForm.selectedAdmins"
            :key="admin.code"
            closable
            @close="removeSelectedAdmin(index)"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ admin.code }} - {{ admin.name }}
          </el-tag>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="addCategoryAdminDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategoryAdmin" :disabled="categoryAdminForm.selectedAdmins.length === 0">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  getCategories, createCategory, updateCategory, deleteCategory,
  getAdminConfigs, createAdminConfig, updateAdminConfig, deleteAdminConfig,
  getDepartmentAdmins, createDepartmentAdmin, deleteDepartmentAdmin,
  getCategoryAdmins, createCategoryAdmin, deleteCategoryAdmin,
  searchStaff
} from '@/api/admin'

export default {
  name: 'AdminIndex',
  data() {
    return {
      activeTab: 'categories',
      isSuperAdmin: false,
      // 工单类别
      categories: [],
      categoriesLoading: false,
      categoryDialogVisible: false,
      categoryDialogTitle: '新增工单类别',
      categoryForm: {
        id: null,
        category_code: '',
        category_name: '',
        description: '',
        sort_order: 0,
        is_active: true
      },
      categoryRules: {
        category_name: [{ required: true, message: '请输入类别名称', trigger: 'blur' }]
      },
      // 系统管理员
      admins: [],
      adminsLoading: false,
      adminDialogVisible: false,
      adminForm: {
        id: null,
        user_id: '',
        user_name: '',
        is_super_admin: false,
        can_manage_form: false,
        can_manage_external: false
      },
      adminRules: {
        user_id: [{ required: true, message: '请选择管理员', trigger: 'blur' }]
      },
      // 部门管理员
      deptAdmins: [],
      deptAdminsLoading: false,
      deptAdminDialogVisible: false,
      deptAdminDialogTitle: '新增部门管理员',
      deptAdminForm: {
        id: null,
        dept_name: '',
        selectedAdmins: []  // 改为数组，支持多选
      },
      deptAdminRules: {
        dept_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
        selectedAdmins: [{ required: true, message: '请至少选择一个管理员', trigger: 'change' }]
      },
      deptAdminStaffSearchResults: [],  // 员工搜索结果
      // 类别管理员
      currentCategory: {},
      categoryAdminDialogVisible: false,
      categoryAdmins: [],
      addCategoryAdminDialogVisible: false,
      categoryAdminForm: {
        selectedAdmins: []  // 改为数组，支持多选
      },
      categoryAdminRules: {
        selectedAdmins: [{ required: true, message: '请至少选择一个管理员', trigger: 'change' }]
      },
      staffSearchResults: []  // 员工搜索结果
    }
  },
  mounted() {
    // 检查权限
    this.isSuperAdmin = this.$store.state.user.is_super_admin || false
    if (!this.isSuperAdmin) {
      this.$message.error('您没有权限访问此页面')
      this.$router.push('/')
      return
    }
    
    this.loadCategories()
    this.loadAdmins()
    this.loadDeptAdmins()
  },
  methods: {
    // 工单类别
    async loadCategories() {
      this.categoriesLoading = true
      try {
        const res = await getCategories()
        if (res.success) {
          this.categories = res.data
        }
      } catch (error) {
        this.$message.error('加载工单类别失败')
      } finally {
        this.categoriesLoading = false
      }
    },
    showCategoryDialog() {
      this.categoryDialogTitle = '新增工单类别'
      this.categoryForm = {
        id: null,
        category_code: '', // 新增时不需要，后端自动生成
        category_name: '',
        description: '',
        sort_order: 0,
        is_active: true
      }
      this.categoryDialogVisible = true
    },
    editCategory(row) {
      this.categoryDialogTitle = '编辑工单类别'
      this.categoryForm = { ...row }
      this.categoryDialogVisible = true
    },
    async saveCategory() {
      this.$refs.categoryForm.validate(async (valid) => {
        if (!valid) return
        try {
          let res
          if (this.categoryForm.id) {
            // 编辑时，不发送category_code（不允许修改）
            const updateData = { ...this.categoryForm }
            delete updateData.category_code
            res = await updateCategory(this.categoryForm.id, updateData)
          } else {
            // 新增时，不发送category_code（后端自动生成）
            const createData = { ...this.categoryForm }
            delete createData.category_code
            res = await createCategory(createData)
            // 如果返回了生成的category_code，更新表单显示
            if (res.success && res.data && res.data.category_code) {
              this.categoryForm.category_code = res.data.category_code
            }
          }
          if (res.success) {
            this.$message.success('保存成功')
            this.categoryDialogVisible = false
            this.loadCategories()
          } else {
            this.$message.error(res.message || '保存失败')
          }
        } catch (error) {
          this.$message.error('保存失败')
        }
      })
    },
    deleteCategory(row) {
      this.$confirm(`确定要删除类别"${row.category_name}"吗？`, '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await deleteCategory(row.id)
          if (res.success) {
            this.$message.success('删除成功')
            this.loadCategories()
          }
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    resetCategoryForm() {
      this.$refs.categoryForm && this.$refs.categoryForm.resetFields()
    },
    manageCategoryAdmins(row) {
      this.currentCategory = row
      this.loadCategoryAdmins(row.id)
      this.categoryAdminDialogVisible = true
    },
    // 系统管理员
    async loadAdmins() {
      this.adminsLoading = true
      try {
        const res = await getAdminConfigs()
        if (res.success) {
          this.admins = res.data
        }
      } catch (error) {
        this.$message.error('加载系统管理员失败')
      } finally {
        this.adminsLoading = false
      }
    },
    showAdminDialog() {
      this.adminForm = {
        id: null,
        user_id: '',
        user_name: '',
        is_super_admin: false,
        can_manage_form: false,
        can_manage_external: false
      }
      this.adminDialogVisible = true
    },
    editAdmin(row) {
      this.adminForm = { ...row }
      this.adminDialogVisible = true
    },
    async saveAdmin() {
      this.$refs.adminForm.validate(async (valid) => {
        if (!valid) return
        try {
          let res
          if (this.adminForm.id) {
            res = await updateAdminConfig(this.adminForm.id, this.adminForm)
          } else {
            res = await createAdminConfig(this.adminForm)
          }
          if (res.success) {
            this.$message.success('保存成功')
            this.adminDialogVisible = false
            this.loadAdmins()
          }
        } catch (error) {
          this.$message.error('保存失败')
        }
      })
    },
    deleteAdmin(row) {
      this.$confirm(`确定要删除管理员"${row.user_name}"吗？`, '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await deleteAdminConfig(row.id)
          if (res.success) {
            this.$message.success('删除成功')
            this.loadAdmins()
          }
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    resetAdminForm() {
      this.$refs.adminForm && this.$refs.adminForm.resetFields()
    },
    // 部门管理员
    async loadDeptAdmins() {
      this.deptAdminsLoading = true
      try {
        const res = await getDepartmentAdmins()
        if (res.success) {
          this.deptAdmins = res.data
        }
      } catch (error) {
        this.$message.error('加载部门管理员失败')
      } finally {
        this.deptAdminsLoading = false
      }
    },
    showDeptAdminDialog() {
      this.deptAdminDialogTitle = '新增部门管理员'
      this.deptAdminForm = {
        id: null,
        dept_name: '',
        selectedAdmins: []
      }
      this.deptAdminStaffSearchResults = []
      this.deptAdminDialogVisible = true
    },
    editDeptAdmin(row) {
      this.deptAdminDialogTitle = '编辑部门管理员'
      // 加载该部门的所有管理员
      const adminsForDept = this.deptAdmins.filter(item => item.dept_name === row.dept_name)
      this.deptAdminForm = {
        id: row.id,
        dept_name: row.dept_name,
        selectedAdmins: adminsForDept.map(item => ({
          code: item.admin_id,
          name: item.admin_name
        }))
      }
      this.deptAdminStaffSearchResults = []
      this.deptAdminDialogVisible = true
    },
    async searchStaffForDeptAdmin(queryString) {
      if (!queryString) {
        this.deptAdminStaffSearchResults = []
        return
      }
      try {
        const res = await searchStaff({ keyword: queryString, limit: 10 })
        if (res.success && res.data) {
          this.deptAdminStaffSearchResults = res.data
        } else {
          this.deptAdminStaffSearchResults = []
        }
      } catch (error) {
        console.error('搜索员工失败:', error)
        this.deptAdminStaffSearchResults = []
      }
    },
    handleDeptAdminSelectChange(value) {
      this.deptAdminForm.selectedAdmins = value
    },
    removeDeptAdminSelected(index) {
      this.deptAdminForm.selectedAdmins.splice(index, 1)
    },
    async saveDeptAdmin() {
      if (this.deptAdminForm.selectedAdmins.length === 0) {
        this.$message.warning('请至少选择一个管理员')
        return
      }
      this.$refs.deptAdminForm.validate(async (valid) => {
        if (!valid) return
        try {
          if (this.deptAdminForm.id) {
            // 编辑模式：先删除该部门的所有管理员，然后重新创建
            const adminsForDept = this.deptAdmins.filter(item => item.dept_name === this.deptAdminForm.dept_name)
            const deletePromises = adminsForDept.map(item => deleteDepartmentAdmin(item.id))
            await Promise.all(deletePromises)
          }
          
          // 批量创建部门管理员
          const promises = this.deptAdminForm.selectedAdmins.map(admin => 
            createDepartmentAdmin({
              dept_name: this.deptAdminForm.dept_name,
              admin_id: admin.code,
              admin_name: admin.name
            })
          )
          const results = await Promise.all(promises)
          
          // 检查是否有失败的
          const failed = results.filter(r => !r.success)
          if (failed.length > 0) {
            this.$message.warning(`成功添加 ${results.length - failed.length} 个管理员，${failed.length} 个添加失败`)
          } else {
            this.$message.success(this.deptAdminForm.id ? '更新成功' : `成功添加 ${results.length} 个管理员`)
          }
          
          this.deptAdminDialogVisible = false
          this.loadDeptAdmins()
        } catch (error) {
          this.$message.error('保存失败')
        }
      })
    },
    deleteDeptAdmin(row) {
      this.$confirm(`确定要删除部门管理员"${row.admin_name}"吗？`, '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await deleteDepartmentAdmin(row.id)
          if (res.success) {
            this.$message.success('删除成功')
            this.loadDeptAdmins()
          }
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    resetDeptAdminForm() {
      this.deptAdminForm = {
        id: null,
        dept_name: '',
        selectedAdmins: []
      }
      this.deptAdminStaffSearchResults = []
      this.$refs.deptAdminForm && this.$refs.deptAdminForm.resetFields()
    },
    // 类别管理员
    async loadCategoryAdmins(categoryId) {
      try {
        const res = await getCategoryAdmins({ category_id: categoryId })
        if (res.success) {
          this.categoryAdmins = res.data
        }
      } catch (error) {
        this.$message.error('加载类别管理员失败')
      }
    },
    showCategoryAdminDialog() {
      this.categoryAdminForm = {
        selectedAdmins: []
      }
      this.staffSearchResults = []
      this.addCategoryAdminDialogVisible = true
    },
    async searchStaffForSelect(queryString) {
      if (!queryString) {
        this.staffSearchResults = []
        return
      }
      try {
        // searchStaff API需要传递keyword参数（与原来的searchStaff方法保持一致）
        const res = await searchStaff({ keyword: queryString, limit: 10 })
        if (res.success && res.data) {
          this.staffSearchResults = res.data
        } else {
          this.staffSearchResults = []
        }
      } catch (error) {
        console.error('搜索员工失败:', error)
        this.staffSearchResults = []
      }
    },
    handleCategoryAdminSelectChange(value) {
      // 当选择改变时，更新已选管理员列表
      this.categoryAdminForm.selectedAdmins = value
    },
    removeSelectedAdmin(index) {
      this.categoryAdminForm.selectedAdmins.splice(index, 1)
    },
    async saveCategoryAdmin() {
      if (this.categoryAdminForm.selectedAdmins.length === 0) {
        this.$message.warning('请至少选择一个管理员')
        return
      }
      try {
        // 批量创建类别管理员
        const promises = this.categoryAdminForm.selectedAdmins.map(admin => 
          createCategoryAdmin({
            category_id: this.currentCategory.id,
            admin_id: admin.code,
            admin_name: admin.name
          })
        )
        const results = await Promise.all(promises)
        
        // 检查是否有失败的
        const failed = results.filter(r => !r.success)
        if (failed.length > 0) {
          this.$message.warning(`成功添加 ${results.length - failed.length} 个管理员，${failed.length} 个添加失败`)
        } else {
          this.$message.success(`成功添加 ${results.length} 个管理员`)
        }
        
        this.addCategoryAdminDialogVisible = false
        this.loadCategoryAdmins(this.currentCategory.id)
      } catch (error) {
        this.$message.error('保存失败')
      }
    },
    deleteCategoryAdmin(row) {
      this.$confirm(`确定要删除类别管理员"${row.admin_name}"吗？`, '提示', {
        type: 'warning'
      }).then(async () => {
        try {
          const res = await deleteCategoryAdmin(row.id)
          if (res.success) {
            this.$message.success('删除成功')
            this.loadCategoryAdmins(this.currentCategory.id)
          }
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    resetCategoryAdminForm() {
      this.categoryAdminForm = {
        selectedAdmins: []
      }
      this.staffSearchResults = []
      this.$refs.categoryAdminForm && this.$refs.categoryAdminForm.resetFields()
    },
    // 员工搜索
    async searchStaff(queryString, cb) {
      if (!queryString) {
        cb([])
        return
      }
      try {
        const res = await searchStaff({ keyword: queryString, limit: 10 })
        if (res.success) {
          cb(res.data || [])
        } else {
          cb([])
        }
      } catch (error) {
        cb([])
      }
    },
    handleStaffSelect(item) {
      this.adminForm.user_id = item.code
      this.adminForm.user_name = item.name
    },
  }
}
</script>

<style lang="scss" scoped>
.admin-index {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
