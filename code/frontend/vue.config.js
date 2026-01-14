// 服务器配置（可通过环境变量覆盖）
const SERVER_IP = process.env.VUE_APP_SERVER_IP || '10.119.9.223'
const BACKEND_PORT = process.env.VUE_APP_BACKEND_PORT || '8081'

module.exports = {
  devServer: {
    port: 3003,
    host: '0.0.0.0', // 允许外部访问
    proxy: {
      '/process': {
        target: `http://${SERVER_IP}:${BACKEND_PORT}`,
        changeOrigin: true,
        ws: true
      }
    }
  },
  publicPath: '/libProcess/',
  outputDir: 'dist',
  assetsDir: 'static',
  lintOnSave: process.env.NODE_ENV === 'development',
  productionSourceMap: false
}

