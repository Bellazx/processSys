<template>
  <div class="work-order-list">
    <div class="page-header">
      <h2>工单管理</h2>
      <el-button type="primary" @click="$router.push('/work-orders/create')">
        新建工单
      </el-button>
    </div>
    
    <el-card>
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane label="我的申请" name="my_applications"></el-tab-pane>
        <el-tab-pane label="待我处理" name="pending_approvals"></el-tab-pane>
      </el-tabs>
      
      <el-table :data="workOrders" v-loading="loading">
        <el-table-column prop="order_no" label="工单编号" width="240" show-overflow-tooltip></el-table-column>
        <el-table-column prop="category_name" label="类别" width="120"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180"></el-table-column>
        <el-table-column label="操作" width="200">
          <template slot-scope="scope">
            <!-- 待我审批标签页 -->
            <template v-if="activeTab === 'pending_approvals'">
              <!-- 待审批状态的工单：显示审批按钮 -->
              <el-button 
                v-if="canApprove(scope.row)" 
                size="mini" 
                type="success"
                @click="approve(scope.row.id)"
              >
                审批
              </el-button>
              <!-- 外派状态的工单：显示提交外派结果按钮 -->
              <el-button 
                v-else-if="canSubmitExternalResult(scope.row)" 
                size="mini" 
                type="primary"
                @click="viewDetail(scope.row.id)"
              >
                提交外派结果
              </el-button>
              <!-- 其他状态：显示查看按钮 -->
              <el-button 
                v-else
                size="mini" 
                @click="viewDetail(scope.row.id)"
              >
                查看
              </el-button>
            </template>
            <!-- 我的申请标签页：显示查看按钮 -->
            <el-button 
              v-if="activeTab === 'my_applications'" 
              size="mini" 
              @click="viewDetail(scope.row.id)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-sizes="[10, 20, 50]"
        :page-size="perPage"
        layout="total, sizes, prev, pager, next"
        :total="total"
      ></el-pagination>
    </el-card>
  </div>
</template>

<script>
import { getWorkOrders } from '@/api/workOrder'
import { mapState } from 'vuex'

export default {
  name: 'WorkOrderList',
  data() {
    return {
      activeTab: 'my_applications',
      workOrders: [],
      loading: false,
      page: 1,
      perPage: 10,
      total: 0,
      isAdmin: false
    }
  },
  computed: {
    ...mapState('user', ['user_id'])
  },
  mounted() {
    // 从路由查询参数中获取filter，如果有则设置activeTab
    if (this.$route.query.filter) {
      this.activeTab = this.$route.query.filter
    }
    this.loadWorkOrders()
  },
  methods: {
    async loadWorkOrders() {
      this.loading = true
      try {
        const res = await getWorkOrders({
          filter: this.activeTab,
          page: this.page,
          per_page: this.perPage
        })
        if (res.success) {
          this.workOrders = res.data.items
          this.total = res.data.total
        }
      } catch (error) {
        this.$message.error('加载工单列表失败')
      } finally {
        this.loading = false
      }
    },
    handleTabClick() {
      this.page = 1
      this.loadWorkOrders()
    },
    handleSizeChange(val) {
      this.perPage = val
      this.loadWorkOrders()
    },
    handleCurrentChange(val) {
      this.page = val
      this.loadWorkOrders()
    },
    viewDetail(id) {
      this.$router.push(`/work-orders/${id}`)
    },
    approve(id) {
      this.$router.push(`/dashboard/work-orders/${id}`)
    },
    canApprove(row) {
      return this.activeTab === 'pending_approvals' && row.status === 'pending'
    },
    canSubmitExternalResult(row) {
      // 外派状态的工单，如果当前用户有外派管理权限，可以提交外派结果
      // 注意：这里只是判断是否显示按钮，实际权限检查在详情页面
      return this.activeTab === 'pending_approvals' && row.status === 'external' && row.is_external
    },
    getStatusType(status) {
      const map = {
        'pending': 'warning',
        'rejected': 'danger',
        'returned': 'warning',  // 已打回显示为warning（待处理状态）
        'completed': 'success',
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
.work-order-list {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
}
</style>

