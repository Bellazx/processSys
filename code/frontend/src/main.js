import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './styles/index.scss'
import axios from './utils/request'

Vue.config.productionTip = false

// 全局错误处理
Vue.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误:', err, info)
  if (vm && vm.$message) {
    vm.$message.error('页面加载失败，请刷新重试')
  }
}

Vue.use(ElementUI)

// 全局配置axios
Vue.prototype.$http = axios

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')

