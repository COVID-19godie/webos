<template>
  <div 
    class="dynamic-island-wrapper"
    @mouseenter="expand"
    @mouseleave="collapse"
  >
    <div 
      class="dynamic-island"
      :class="{ 
        expanded: isExpanded,
        'has-activity': hasActivity,
        pulse: isPulsing
      }"
      @click="toggleExpand"
    >
      <!-- 收缩状态：时间显示 -->
      <div class="island-content compact" v-show="!isExpanded">
        <div class="time-display">
          <span class="time">{{ currentTime }}</span>
          <span class="date">{{ currentDate }}</span>
        </div>
        <div class="activity-indicator" v-if="hasActivity">
          <div class="activity-dot"></div>
        </div>
      </div>

      <!-- 展开状态 -->
      <div class="island-content expanded" v-show="isExpanded">
        <div class="expanded-left">
          <div class="datetime-full">
            <div class="time-large">{{ currentTime }}</div>
            <div class="date-full">{{ fullDate }}</div>
          </div>
        </div>
        
        <div class="expanded-center">
          <div class="greeting">{{ greeting }}</div>
          <div class="timer-row">
            <span class="timer-label">计时器</span>
            <span class="timer-value">{{ formattedTimer }}</span>
          </div>
          <div class="running-apps" v-if="runningApps.length">
            <div class="apps-label">运行中</div>
            <div class="apps-icons">
              <div 
                v-for="app in runningApps.slice(0, 5)" 
                :key="app.id" 
                class="mini-app-icon"
                :title="app.title"
                @click.stop="focusApp(app)"
              >
                <i :class="getAppIcon(app)"></i>
              </div>
              <span v-if="runningApps.length > 5" class="more-apps">+{{ runningApps.length - 5 }}</span>
            </div>
          </div>
        </div>

        <div class="expanded-right">
          <div class="quick-actions">
            <button class="action-btn" @click.stop="$emit('open-launcher')" title="启动台">
              <i class="fa-solid fa-th-large"></i>
            </button>
            <button class="action-btn" @click.stop="$emit('open-finder')" title="访达">
              <i class="fa-solid fa-folder"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWindowStore } from '@/stores/windowStore'

const emit = defineEmits(['open-launcher', 'open-finder'])
const winStore = useWindowStore()

const isExpanded = ref(false)
const isPulsing = ref(false)
const currentTime = ref('')
const currentDate = ref('')
const fullDate = ref('')
const timerSeconds = ref(40 * 60)
let timerInterval = null

// 计算运行中的应用
const runningApps = computed(() => winStore.windows.filter(w => !w.isMinimized))
const hasActivity = computed(() => runningApps.value.length > 0)

// 问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了，注意休息 🌙'
  if (hour < 9) return '早上好 ☀️'
  if (hour < 12) return '上午好 🌤️'
  if (hour < 14) return '中午好 🌞'
  if (hour < 18) return '下午好 🌅'
  if (hour < 22) return '晚上好 🌆'
  return '夜深了，注意休息 🌙'
})

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit'
  })
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    weekday: 'short'
  })
  fullDate.value = now.toLocaleDateString('zh-CN', { 
    year: 'numeric',
    month: 'long', 
    day: 'numeric',
    weekday: 'long'
  })
}

const formattedTimer = computed(() => {
  const total = Math.max(0, timerSeconds.value)
  const mins = String(Math.floor(total / 60)).padStart(2, '0')
  const secs = String(total % 60).padStart(2, '0')
  return `${mins}:${secs}`
})

// 展开/收起
const expand = () => {
  isExpanded.value = true
}

const collapse = () => {
  isExpanded.value = false
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

// 聚焦应用
const focusApp = (app) => {
  winStore.activateWindow(app.id)
  collapse()
}

// 获取应用图标
const getAppIcon = (app) => {
  if (app.icon) return app.icon
  if (app.data?.icon_class) return app.data.icon_class
  if (app.type === 'category') return 'fa-solid fa-folder'
  return 'fa-solid fa-file'
}

// 脉冲动画
const triggerPulse = () => {
  isPulsing.value = true
  setTimeout(() => {
    isPulsing.value = false
  }, 600)
}

let timer = null
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  timerInterval = setInterval(() => {
    if (timerSeconds.value > 0) timerSeconds.value -= 1
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (timerInterval) clearInterval(timerInterval)
})

// 暴露方法给父组件
defineExpose({ triggerPulse })
</script>

<style scoped>
.dynamic-island-wrapper {
  position: fixed;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  pointer-events: auto;
}

.dynamic-island {
  background: rgba(0, 0, 0, 0.85);
  border-radius: 28px;
  padding: 8px 16px;
  min-width: 140px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  overflow: hidden;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.dynamic-island:hover {
  transform: scale(1.02);
}

.dynamic-island.expanded {
  min-width: 380px;
  height: 100px;
  border-radius: 36px;
  padding: 12px 20px;
}

.dynamic-island.has-activity::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, 
    transparent 30%,
    rgba(100, 200, 255, 0.3) 50%,
    transparent 70%
  );
  border-radius: inherit;
  z-index: -1;
  animation: shimmer 3s ease-in-out infinite;
}

.dynamic-island.pulse {
  animation: island-pulse 0.6s ease-out;
}

@keyframes island-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.08); box-shadow: 0 0 30px rgba(100, 200, 255, 0.6); }
  100% { transform: scale(1); }
}

@keyframes shimmer {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

/* 收缩状态内容 */
.island-content.compact {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-display {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.time {
  color: white;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.date {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.activity-indicator {
  display: flex;
  align-items: center;
}

.activity-dot {
  width: 6px;
  height: 6px;
  background: #4ade80;
  border-radius: 50%;
  animation: dot-pulse 2s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* 展开状态内容 */
.island-content.expanded {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 16px;
}

.expanded-left {
  flex-shrink: 0;
}

.datetime-full {
  text-align: left;
}

.time-large {
  color: white;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1.2;
}

.date-full {
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
  margin-top: 2px;
}

.expanded-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.greeting {
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 500;
}

.running-apps {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timer-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.timer-label {
  color: rgba(255, 255, 255, 0.5);
}

.timer-value {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.apps-label {
  color: rgba(255, 255, 255, 0.4);
  font-size: 10px;
}

.apps-icons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mini-app-icon {
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.mini-app-icon:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.more-apps {
  color: rgba(255, 255, 255, 0.5);
  font-size: 10px;
  margin-left: 4px;
}

.expanded-right {
  flex-shrink: 0;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.action-btn:active {
  transform: scale(0.95);
}

/* 响应式调整 */
@media (max-width: 480px) {
  .dynamic-island.expanded {
    min-width: 320px;
    height: 90px;
  }
  
  .time-large {
    font-size: 20px;
  }
  
  .greeting {
    font-size: 12px;
  }
}
</style>
