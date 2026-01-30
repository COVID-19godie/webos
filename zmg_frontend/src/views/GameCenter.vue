<template>
  <div class="app-page">
    <div class="card">
      <div class="icon">
        <i class="fa-solid fa-gamepad"></i>
      </div>
      <h1>游戏中心</h1>
      <p>这里汇聚课堂互动小游戏与教学闯关内容，正在持续更新。</p>
      <div class="actions">
        <button class="primary-btn" @click="openStore">去应用商店</button>
        <button class="ghost-btn" @click="openWatch">去观看中心</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const openStore = () => window.open('/store', '_blank')
const openWatch = () => window.open('/watch', '_blank')
</script>

<style scoped>
.app-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fb;
  color: #1f2937;
}

.card {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  width: min(520px, 90vw);
  text-align: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.icon {
  font-size: 48px;
  color: #845ef7;
  margin-bottom: 12px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 18px;
}

.primary-btn,
.ghost-btn {
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 14px;
  cursor: pointer;
}

.primary-btn {
  background: #845ef7;
  color: #fff;
  border-color: #845ef7;
}
</style>
