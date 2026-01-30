import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { createPinia } from 'pinia'
import router from './router'

// 🟢 新增：直接引入本地的 FontAwesome 样式
import '@fortawesome/fontawesome-free/css/all.min.css'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')