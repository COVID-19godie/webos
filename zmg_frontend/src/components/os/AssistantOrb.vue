<template>
  <div class="assistant-orb">
    <div class="orb" :class="{ open }" @click="toggle">
      <i class="fa-solid fa-wand-magic-sparkles"></i>
    </div>
    <div v-if="open" class="assistant-panel">
      <div class="panel-header">
        <div class="title">轻量AI助手</div>
        <button class="close-btn" @click="toggle">×</button>
      </div>
      <div class="panel-body">
        <div v-for="(msg, idx) in messages" :key="idx" class="msg" :class="msg.role">
          <div class="bubble">{{ msg.text }}</div>
          <div v-if="msg.results?.length" class="results">
            <div v-for="item in msg.results" :key="item.id" class="result-item" @click="openLink(item.link)">
              <div class="result-title">{{ item.title }}</div>
              <div class="result-meta">相关度 {{ item.score }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="panel-input">
        <input v-model="input" placeholder="说点什么，比如：教育类H5应用" @keydown.enter="send" />
        <button @click="send">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { appStoreApi } from '@/api'

const open = ref(false)
const input = ref('')
const messages = ref([
  { role: 'assistant', text: '我是轻量AI助手，可以帮你找相关应用。' }
])

const toggle = () => { open.value = !open.value }

const scoreItem = (item, query) => {
  const q = query.toLowerCase()
  const text = `${item.title} ${item.summary || ''} ${item.tags?.map(t => t.name).join(' ')}`.toLowerCase()
  if (!q) return 0
  let score = 0
  q.split(/\s+/).forEach(term => {
    if (!term) return
    const count = text.split(term).length - 1
    score += count * 10
    if (item.title?.toLowerCase().includes(term)) score += 5
  })
  return score
}

const send = async () => {
  if (!input.value.trim()) return
  const query = input.value.trim()
  messages.value.push({ role: 'user', text: query })
  messages.value.push({ role: 'assistant', text: '正在为你查找相关内容...' })
  input.value = ''
  try {
    const res = await appStoreApi.list({ search: query })
    const items = res.data.results || res.data || []
    const ranked = items
      .map(item => ({ ...item, score: scoreItem(item, query) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
    messages.value.pop()
    messages.value.push({
      role: 'assistant',
      text: ranked.length ? '我找到这些相关内容：' : '暂未找到匹配内容',
      results: ranked
    })
  } catch (err) {
    messages.value.pop()
    messages.value.push({ role: 'assistant', text: '搜索失败，请稍后再试。' })
  }
}

const openLink = (link) => {
  if (link) window.open(link, '_blank')
}
</script>

<style scoped>
.assistant-orb { position: fixed; right: 22px; bottom: 110px; z-index: 9999; }
.orb {
  width: 54px; height: 54px; border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #ffffff, #c7d2fe);
  box-shadow: 0 12px 28px rgba(0,0,0,0.2);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: transform 0.2s ease;
}
.orb:hover { transform: scale(1.08); }
.orb.open { background: radial-gradient(circle at 30% 30%, #e0f2ff, #93c5fd); }
.assistant-panel {
  position: absolute; right: 0; bottom: 70px;
  width: 320px; max-height: 420px;
  background: #fff; border-radius: 16px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.2);
  display: flex; flex-direction: column; overflow: hidden;
}
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid #eee; }
.panel-header .title { font-weight: 600; }
.close-btn { border: none; background: transparent; font-size: 20px; cursor: pointer; }
.panel-body { padding: 10px; overflow-y: auto; max-height: 300px; }
.msg { margin-bottom: 10px; }
.msg.user .bubble { background: #dbeafe; align-self: flex-end; }
.msg.assistant .bubble { background: #f1f5f9; }
.bubble { padding: 8px 10px; border-radius: 10px; font-size: 13px; }
.results { margin-top: 6px; display: grid; gap: 6px; }
.result-item { border: 1px solid #e5e7eb; border-radius: 10px; padding: 8px; cursor: pointer; }
.result-title { font-weight: 600; font-size: 12px; }
.result-meta { font-size: 11px; color: #6b7280; }
.panel-input { display: flex; gap: 6px; padding: 10px; border-top: 1px solid #eee; }
.panel-input input { flex: 1; padding: 6px 8px; border-radius: 10px; border: 1px solid #e5e7eb; }
.panel-input button { padding: 6px 10px; border-radius: 10px; border: none; background: var(--accent); color: #fff; cursor: pointer; }
</style>
