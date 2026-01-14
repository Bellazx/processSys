<template>
  <div class="work-order-management">
    <div class="page-header">
      <h2>工单管理</h2>
      <div>
        <el-button type="success" @click="exportExcel" :loading="exporting">
          <i class="el-icon-download"></i> 导出Excel
        </el-button>
      </div>
    </div>
    
    <el-card>
      <!-- 过滤条件 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="工单编号">
          <el-input v-model="filters.order_no" placeholder="请输入工单编号" clearable style="width: 200px"></el-input>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="filters.category_id" placeholder="请选择类别" clearable style="width: 200px">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.category_name"
              :value="cat.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="申请人">
          <el-select
            v-model="filters.applicant_id"
            filterable
            remote
            :remote-method="searchApplicant"
            :loading="applicantSearchLoading"
            placeholder="请输入姓名或学工号搜索"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="staff in applicantList"
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
        <el-form-item label="审批人">
          <el-select
            v-model="filters.approver_id"
            filterable
            remote
            :remote-method="searchApprover"
            :loading="approverSearchLoading"
            placeholder="请输入姓名或学工号搜索"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="staff in approverList"
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
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="待处理" value="pending"></el-option>
            <el-option label="已拒绝" value="rejected"></el-option>
            <el-option label="已完成" value="completed"></el-option>
            <el-option label="已终止" value="terminated"></el-option>
            <el-option label="外派" value="external"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadWorkOrders">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 工单列表 -->
      <el-table :data="workOrders" v-loading="loading" border style="width: 100%">
        <el-table-column prop="order_no" label="工单编号" min-width="200" fixed="left" show-overflow-tooltip></el-table-column>
        <el-table-column prop="category_name" label="类别" min-width="120"></el-table-column>
        <el-table-column prop="applicant_name" label="申请人" min-width="100"></el-table-column>
        <el-table-column prop="applicant_dept" label="申请人部门" min-width="150" show-overflow-tooltip></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_approver_name" label="当前审批人" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="160"></el-table-column>
        <el-table-column prop="complete_time" label="完成时间" width="160"></el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" @click="viewDetail(scope.row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="perPage"
        layout="total, sizes, prev, pager, next"
        :total="total"
        style="margin-top: 20px; text-align: right;"
      ></el-pagination>
    </el-card>
  </div>
</template>

<script>
import { getWorkOrdersManagement, exportWorkOrders } from '@/api/workOrder'
import { getCategories, searchStaff } from '@/api/admin'

export default {
  name: 'WorkOrderManagement',
  data() {
    return {
      workOrders: [],
      categories: [],
      loading: false,
      exporting: false,
      page: 1,
      perPage: 20,
      total: 0,
      filters: {
        order_no: '',
        category_id: '',
        applicant_id: '',
        approver_id: '',
        status: ''
      },
      applicantList: [],
      approverList: [],
      applicantSearchLoading: false,
      approverSearchLoading: false
    }
  },
  mounted() {
    try {
      // 从路由参数中获取初始过滤条件
      if (this.$route.query.category_id) {
        this.filters.category_id = parseInt(this.$route.query.category_id)
      }
      this.loadCategories()
      this.loadWorkOrders()
    } catch (error) {
      console.error('Management组件mounted错误:', error)
      this.$message.error('页面初始化失败，请刷新重试')
    }
  },
  methods: {
    async loadCategories() {
      try {
        const res = await getCategories({ is_active: true })
        if (res.success) {
          this.categories = res.data || []
        }
      } catch (error) {
        // 忽略错误，不影响页面显示
      }
    },
    async loadWorkOrders() {
      this.loading = true
      try {
        const params = {
          page: this.page,
          per_page: this.perPage
        }
        
        // 添加过滤条件
        if (this.filters.order_no) {
          params.order_no = this.filters.order_no
        }
        if (this.filters.category_id) {
          params.category_id = this.filters.category_id
        }
        if (this.filters.applicant_id) {
          params.applicant_id = this.filters.applicant_id
        }
        if (this.filters.approver_id) {
          params.approver_id = this.filters.approver_id
        }
        if (this.filters.status) {
          params.status = this.filters.status
        }
        
        const res = await getWorkOrdersManagement(params)
        
        if (res.success) {
          this.workOrders = res.data.items || []
          this.total = res.data.total || 0
        } else {
          // 显示后端返回的错误信息
          const errorMsg = res.message || '加载工单列表失败'
          this.$message.error(errorMsg)
          
          // 如果是权限错误，显示更友好的提示
          if (errorMsg.includes('无权访问') || errorMsg.includes('管理员权限')) {
            this.$message.warning('您没有权限访问此页面，请联系系统管理员')
          }
        }
      } catch (error) {
        // 处理网络错误或其他异常
        let errorMsg = '加载工单列表失败'
        if (error.response && error.response.data && error.response.data.message) {
          errorMsg = error.response.data.message
        } else if (error.message) {
          errorMsg = error.message
        }
        this.$message.error(errorMsg)
        
        // 如果是权限错误，显示更友好的提示
        if (errorMsg.includes('无权访问') || errorMsg.includes('管理员权限') || (error.response && error.response.status === 403)) {
          this.$message.warning('您没有权限访问此页面，请联系系统管理员')
        }
      } finally {
        this.loading = false
      }
    },
    resetFilters() {
      this.filters = {
        order_no: '',
        category_id: '',
        applicant_id: '',
        approver_id: '',
        status: ''
      }
      this.applicantList = []
      this.approverList = []
      this.page = 1
      this.loadWorkOrders()
    },
    async searchApplicant(query) {
      if (!query) {
        this.applicantList = []
        return
      }
      this.applicantSearchLoading = true
      try {
        const res = await searchStaff({ keyword: query })
        if (res.success) {
          this.applicantList = res.data || []
        }
      } catch (error) {
        // 忽略错误
      } finally {
        this.applicantSearchLoading = false
      }
    },
    async searchApprover(query) {
      if (!query) {
        this.approverList = []
        return
      }
      this.approverSearchLoading = true
      try {
        const res = await searchStaff({ keyword: query })
        if (res.success) {
          this.approverList = res.data || []
        }
      } catch (error) {
        // 忽略错误
      } finally {
        this.approverSearchLoading = false
      }
    },
    handleSizeChange(val) {
      this.perPage = val
      this.page = 1
      this.loadWorkOrders()
    },
    handleCurrentChange(val) {
      this.page = val
      this.loadWorkOrders()
    },
    viewDetail(id) {
      this.$router.push({
        path: `/work-orders/${id}`,
        query: { from: 'management' }
      })
    },
    async exportExcel() {
      this.exporting = true
      try {
        const params = {}
        
        // 添加过滤条件
        if (this.filters.order_no) params.order_no = this.filters.order_no
        if (this.filters.category_id) params.category_id = this.filters.category_id
        if (this.filters.applicant_id) params.applicant_id = this.filters.applicant_id
        if (this.filters.approver_id) params.approver_id = this.filters.approver_id
        if (this.filters.status) params.status = this.filters.status
        
        // 使用API调用导出Excel
        const res = await exportWorkOrders(params)
        
        // res.data应该是blob对象（因为responseType: 'blob'）
        const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        })
        
        // 创建Blob对象并下载
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `工单列表_${new Date().toISOString().slice(0, 10)}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        this.$message.success('导出成功')
      } catch (error) {
        console.error('导出失败:', error)
        let errorMsg = '导出失败'
        if (error.response) {
          if (error.response.status === 403) {
            errorMsg = '无权导出工单'
          } else if (error.response.data) {
            // 如果响应是blob，尝试解析错误信息
            if (error.response.data instanceof Blob) {
              try {
                const reader = new FileReader()
                reader.onload = () => {
                  try {
                    const errorData = JSON.parse(reader.result)
                    errorMsg = errorData.message || errorMsg
                  } catch (e) {
                    errorMsg = '导出失败'
                  }
                }
                reader.readAsText(error.response.data)
              } catch (e) {
                errorMsg = '导出失败'
              }
            } else if (error.response.data.message) {
              errorMsg = error.response.data.message
            }
          }
        } else if (error.message) {
          errorMsg = error.message
        }
        this.$message.error(errorMsg)
      } finally {
        this.exporting = false
      }
    },
    getStatusType(status) {
      const map = {
        'pending': 'warning',
        'rejected': 'danger',
        'returned': 'warning',  // 已打回显示为warning（待处理状态）
        'completed': 'success',
        'terminated': 'info',
        'external': 'warning',
        'draft': 'info',
        'cancelled': 'info'
      }
      return map[status] || ''
    },
    getStatusText(status) {
      const map = {
        'pending': '待处理',
        'rejected': '已拒绝',
        'returned': '已打回',  // 打回的工单显示为"已打回"
        'completed': '已完成',
        'terminated': '已终止',
        'external': '外派',
        'draft': '草稿',
        'cancelled': '已撤单',
        // 兼容旧数据
        'approved': '已完成'  // 旧数据：已批准 -> 已完成
      }
      return map[status] || status
    }
  }
}
</script>

<style lang="scss" scoped>
.work-order-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .filter-form {
    margin-bottom: 20px;
  }
}
</style>

