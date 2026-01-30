<template>
  <div 
    v-show="visible"
    class="context-menu glass-panel"
    :style="{ left: x + 'px', top: y + 'px' }"
    @click.stop
    @contextmenu.prevent
  >
    <ul>
      <li 
        v-for="(item, index) in items" 
        :key="index"
        class="menu-item"
        :class="{ 'danger': item.danger, 'separator': item.separator, 'has-children': item.children }"
        @click="handleItemClick(item)"
        @mouseenter="activeSubMenu = index"
        @mouseleave="activeSubMenu = null"
      >
        <div v-if="item.separator" class="separator-line"></div>

        <div v-else class="menu-content">
          <div class="left-col">
            <i :class="item.icon" class="menu-icon"></i>
            <span>{{ item.label }}</span>
          </div>
          <i v-if="item.children" class="fa-solid fa-chevron-right arrow-icon"></i>
        </div>

        <div 
          v-if="item.children && activeSubMenu === index" 
          class="sub-menu glass-panel"
        >
          <ul>
            <li 
              v-for="(subItem, subIndex) in item.children" 
              :key="subIndex"
              class="menu-item"
              @click.stop="handleItemClick(subItem)"
            >
              <div class="menu-content">
                <i :class="subItem.icon" class="menu-icon"></i>
                <span>{{ subItem.label }}</span>
              </div>
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  visible: Boolean,
  x: Number,
  y: Number,
  items: Array
})

const emit = defineEmits(['close'])
const activeSubMenu = ref(null)

const handleItemClick = (item) => {
  if (item.children) return // 如果有子菜单，点击不关闭
  
  if (item.action) {
    item.action()
  }
  emit('close')
}
</script>

<style scoped>
.context-menu {
  position: fixed;
  z-index: 99999;
  width: 200px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 8px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
  padding: 5px 0;
  border: 1px solid rgba(0,0,0,0.05);
}

.menu-item {
  list-style: none;
  padding: 0;
  position: relative;
}

.menu-content {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #333;
  transition: background 0.1s;
}

.left-col {
  display: flex;
  align-items: center;
}

.menu-item:hover > .menu-content {
  background: #007aff;
  color: white;
}

.menu-icon {
  width: 20px;
  text-align: center;
  margin-right: 8px;
}

.arrow-icon {
  font-size: 10px;
  opacity: 0.6;
}

/* 分割线 */
.separator-line {
  height: 1px;
  background: rgba(0,0,0,0.1);
  margin: 4px 0;
}

.menu-item.danger .menu-content { color: #ff3b30; }
.menu-item.danger:hover .menu-content { background: #ff3b30; color: white; }

/* 二级菜单样式 */
.sub-menu {
  position: absolute;
  left: 100%; /* 显示在右侧 */
  top: -5px;
  width: 180px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 8px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
  padding: 5px 0;
  margin-left: 5px; /* 间距 */
  border: 1px solid rgba(0,0,0,0.05);
}
</style>