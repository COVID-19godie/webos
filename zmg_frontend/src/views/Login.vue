<template>
  <div class="login-container">
    <div class="login-card glass-effect">
      <div class="avatar-circle">
        <i class="fa-solid fa-user"></i>
      </div>
      <h2>ZMG Cloud OS</h2>
      <p class="subtitle">请登录以进入云桌面</p>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <input v-model="username" type="text" placeholder="用户名" required />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="密码" required />
        </div>
        
        <button type="submit" :disabled="loading">
          <span v-if="loading"><i class="fa-solid fa-spinner fa-spin"></i> 登录中...</span>
          <span v-else>进入系统</span>
        </button>
      </form>
      
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, tenantApi } from '@/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''
  
  try {
    // 调用我们刚才定义的 API
    const res = await authApi.login(username.value, password.value)
    
    // 保存 Token
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    if (res.data.user_id) {
      localStorage.setItem('user_id', String(res.data.user_id))
    }
    if (res.data.username) {
      localStorage.setItem('username', res.data.username)
    }
    if (res.data.role) {
      localStorage.setItem('user_role', res.data.role)
    }

    try {
      const tenantRes = await tenantApi.list()
      const tenantList = tenantRes.data || []
      if (tenantList.length) {
        localStorage.setItem('current_tenant_id', String(tenantList[0].id))
      }
    } catch (e) {
      console.warn('读取租户失败', e)
    }
    
    // 跳转到桌面
    router.push('/')
  } catch (err) {
    console.error(err)
    errorMsg.value = '登录失败：用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  width: 100vw;
  // 默认壁纸，之后可以替换
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.login-card {
  width: 360px;
  padding: 40px;
  border-radius: 24px;
  text-align: center;
  color: white;
  
  .avatar-circle {
    width: 80px; height: 80px;
    background: rgba(255,255,255,0.3);
    border-radius: 50%;
    margin: 0 auto 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 32px;
  }
  
  h2 { margin: 0 0 10px; font-weight: 600; }
  .subtitle { opacity: 0.8; margin-bottom: 30px; font-size: 0.9em; }
  
  .input-group {
    margin-bottom: 15px;
    input {
      width: 100%;
      padding: 12px 20px;
      border-radius: 12px;
      border: none;
      background: rgba(255,255,255,0.9);
      font-size: 16px;
      outline: none;
      transition: all 0.3s;
      
      &:focus {
        background: white;
        box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.5);
      }
    }
  }
  
  button {
    width: 100%;
    padding: 12px;
    border-radius: 12px;
    border: none;
    background: #007aff; // iOS Blue
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 10px;
    transition: background 0.2s;
    
    &:hover { background: #0062cc; }
    &:disabled { opacity: 0.7; cursor: not-allowed; }
  }
  
  .error-msg {
    color: #ff4d4f;
    margin-top: 15px;
    font-size: 0.9em;
    background: rgba(0,0,0,0.2);
    padding: 5px;
    border-radius: 4px;
  }
}
</style>