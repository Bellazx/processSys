<template>
  <div class="dashboard-container" v-loading="loading">
    <h2>首页</h2>
    
    <!-- 类别筛选（管理员可见） -->
    <div v-if="isAdmin && categories.length > 0" class="category-filter" style="margin-bottom: 20px;">
      <el-select v-model="selectedCategoryId" placeholder="选择类别查看统计" clearable @change="loadStats" style="width: 300px">
        <el-option label="全部类别" :value="null"></el-option>
        <el-option
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.category_name"
          :value="cat.id"
        ></el-option>
      </el-select>
    </div>
    
    <div class="stats-row" v-if="!loading">
      <div class="stat-card" v-for="(stat, index) in stats" :key="index" :style="{ background: stat.color }">
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>
    
    <!-- 按类别统计表格（管理员可见） -->
    <el-card v-if="isAdmin && !selectedCategoryId" class="category-stats-card" style="margin-top: 30px">
      <div slot="header">
        <span>按类别统计</span>
      </div>
      <el-table :data="categoryStats" border v-loading="categoryStatsLoading">
        <el-table-column prop="category_name" label="类别名称" width="200"></el-table-column>
        <el-table-column prop="total" label="总工单数" width="120" align="center"></el-table-column>
        <el-table-column prop="pending" label="待处理" width="120" align="center"></el-table-column>
        <el-table-column prop="completed" label="已完成" width="120" align="center"></el-table-column>
        <el-table-column prop="rejected" label="已拒绝" width="120" align="center"></el-table-column>
        <el-table-column label="操作" width="150">
          <template slot-scope="scope">
            <el-button size="mini" @click="viewCategoryOrders(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <div class="quick-actions" v-if="!loading">
      <h3>快速入口</h3>
      <el-row :gutter="20">
        <el-col 
          :span="6" 
          v-for="category in categories" 
          :key="category.id"
        >
          <el-card 
            class="category-card" 
            @click.native="handleCategoryClick(category)"
            shadow="hover"
          >
            <div class="category-name">{{ category.category_name }}</div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { getDashboardStats } from '@/api/workOrder'
import { getCategories } from '@/api/admin'
import { getFormConfigs } from '@/api/formConfig'

export default {
  name: 'Dashboard',
  data() {
    return {
      stats: [],
      categories: [],
      categoryStats: [],
      loading: true,
      categoryStatsLoading: false,
      selectedCategoryId: null,
      isAdmin: false,
      userType: 'normal'
    }
  },
  mounted() {
    // 路由守卫已经处理了认证，这里直接加载数据
    // 如果store中没有用户信息，说明认证失败，但路由守卫应该已经跳转到登录页了
    if (this.$store.state.user.user_id) {
      this.loadData()
    } else {
      // 如果确实没有用户信息，尝试获取一次（可能是路由守卫的异步问题）
      console.log('Dashboard: store中没有用户信息，尝试获取...')
      this.$store.dispatch('user/getUserInfo').then(() => {
        this.loadData()
      }).catch(() => {
        // 获取失败，路由守卫应该已经处理了跳转
        console.log('Dashboard: 获取用户信息失败')
      })
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        // 加载统计数据
        await this.loadStats()
        
        // 加载工单类别（只显示有已发布表单配置的类别）
        await this.loadCategories()
        
        // 如果是管理员且没有选择类别，加载按类别统计
        if (this.isAdmin && !this.selectedCategoryId) {
          this.loadCategoryStats()
        }
      } catch (error) {
        this.$message.error('加载数据失败')
      } finally {
        this.loading = false
      }
    },
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
        console.error('加载工单类别失败:', error)
        this.categories = []
      }
    },
    async loadStats() {
      try {
        const params = {}
        if (this.selectedCategoryId) {
          params.category_id = this.selectedCategoryId
        }
        const statsRes = await getDashboardStats(params)
        if (statsRes.success) {
          this.userType = statsRes.data.user_type || 'normal'
          this.isAdmin = ['super_admin', 'category_admin'].includes(this.userType)
          this.formatStats(statsRes.data)
        }
      } catch (error) {
        this.$message.error('加载统计数据失败')
      }
    },
    async loadCategoryStats() {
      if (!this.isAdmin) return
      this.categoryStatsLoading = true
      try {
        // 为每个类别加载统计数据
        const statsPromises = this.categories.map(async (category) => {
          try {
            const res = await getDashboardStats({ category_id: category.id })
            if (res.success && res.data.total_orders !== undefined) {
              return {
                category_id: category.id,
                category_name: category.category_name,
                total: res.data.total_orders || 0,
                pending: res.data.pending_orders || 0,
                completed: res.data.completed_orders || 0,
                rejected: res.data.rejected_orders || 0,
                pending: res.data.pending_orders || 0
              }
            }
          } catch (error) {
            console.error(`加载类别 ${category.category_name} 统计失败:`, error)
          }
          return null
        })
        
        const results = await Promise.all(statsPromises)
        this.categoryStats = results.filter(item => item !== null)
      } catch (error) {
        this.$message.error('加载类别统计失败')
      } finally {
        this.categoryStatsLoading = false
      }
    },
    formatStats(data) {
      const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
      this.stats = []
      
      if (data.total_orders !== undefined) {
        // 管理员视图（超级管理员或类别管理员）
        // 统计口径：已完成、已拒绝、待处理、总工单数
        this.stats = [
          { label: '总工单数', value: data.total_orders || 0, color: colors[0] },
          { label: '待处理', value: data.pending_orders || 0, color: colors[1] },
          { label: '已完成', value: data.completed_orders || 0, color: colors[2] },
          { label: '已拒绝', value: data.rejected_orders || 0, color: colors[3] }
        ]
      } else {
        // 普通用户视图
        // 统计口径：已完成、已拒绝、待处理、总工单数
        this.stats = [
          { label: '总工单数', value: data.my_applications || 0, color: colors[0] },
          { label: '待处理', value: data.my_pending || 0, color: colors[1] },
          { label: '已完成', value: data.my_completed || 0, color: colors[2] },
          { label: '已拒绝', value: data.my_rejected || 0, color: colors[3] },
          { label: '待我处理', value: data.pending_approvals || 0, color: colors[4] }
        ]
      }
    },
    viewCategoryStats(row) {
      // 选择该类别并重新加载统计
      this.selectedCategoryId = row.category_id
      this.loadStats()
    },
    viewCategoryOrders(row) {
      // 跳转到工单管理页面，并过滤该类别
      this.$router.push({
        path: '/work-orders/management',
        query: { category_id: row.category_id }
      })
    },
    handleCategoryClick(category) {
      this.$router.push({
        path: '/work-orders/create',
        query: { category_id: category.id }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  h2 {
    margin-bottom: 20px;
  }
  
  .category-filter {
    margin-bottom: 20px;
  }
  
  .stats-row {
    margin-bottom: 30px;
    display: flex;
    gap: 20px;
    flex-wrap: nowrap;
    
    .stat-card {
      flex: 1;
      padding: 20px;
      border-radius: 4px;
      color: #fff;
      text-align: center;
      cursor: pointer;
      transition: transform 0.2s;
      min-width: 0; // 防止flex子项溢出
      
      &:hover {
        transform: translateY(-5px);
      }
      
      .stat-value {
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 10px;
      }
      
      .stat-label {
        font-size: 14px;
      }
    }
  }
  
  .category-stats-card {
    .el-table {
      margin-top: 10px;
    }
  }
  
  .quick-actions {
    margin-top: 30px;
    
    h3 {
      margin-bottom: 20px;
    }
    
    .category-card {
      cursor: pointer;
      text-align: center;
      min-height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
      
      &:hover {
        transform: translateY(-5px);
      }
      
      .category-name {
        font-size: 16px;
        font-weight: bold;
      }
    }
  }
}
</style>

