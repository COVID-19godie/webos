<template>
  <router-view></router-view>
  <AssistantOrb />
</template>

<script setup>
import AssistantOrb from '@/components/os/AssistantOrb.vue'
</script>

<style>
/* 简单的全局重置，确保占满全屏 */
html, body, #app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden; /* 防止出现滚动条，更有系统的感觉 */
}
</style>