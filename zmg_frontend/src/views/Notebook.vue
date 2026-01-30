<template>
  <div class="notebook-page">
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="title">电子黑板</div>
        <button class="primary-btn" @click="createNote">
          <i class="fa-solid fa-plus"></i> 新建
        </button>
      </div>
      <div class="note-list">
        <div
          v-for="note in notes"
          :key="note.id"
          class="note-item"
          :class="{ active: note.id === activeId }"
          @click="selectNote(note.id)"
        >
          <div class="note-title">{{ note.title }}</div>
          <div class="note-meta">{{ formatDate(note.updatedAt) }}</div>
        </div>
      </div>
    </div>

    <div class="editor-area">
      <div class="toolbar">
        <input
          v-model="activeTitle"
          class="title-input"
          placeholder="笔记标题"
          @blur="syncTitle"
        />
        <div class="toolbar-actions">
          <button class="ghost-btn" @click="formatText('bold')"><b>B</b></button>
          <button class="ghost-btn" @click="formatText('italic')"><i>I</i></button>
          <button class="ghost-btn" @click="formatText('underline')"><u>U</u></button>
          <button class="ghost-btn" @click="formatText('insertUnorderedList')">• 列表</button>
          <label class="ghost-btn file-btn">
            导入 Word/PDF
            <input type="file" accept=".docx,.pdf" @change="onImportFile" />
          </label>
          <button class="ghost-btn" @click="saveNotes">保存</button>
          <button class="danger-btn" @click="removeNote">删除</button>
        </div>
      </div>

      <div class="editor-body">
        <div class="editor-pane">
          <div
            ref="editorRef"
            class="rich-editor"
            contenteditable="true"
            @input="onEditorInput"
          ></div>
        </div>
        <div class="preview-pane">
          <div class="preview-title">导入预览</div>
          <div v-if="pdfUrl" class="pdf-preview">
            <VuePdfEmbed :source="pdfUrl" class="pdf-content" />
            <button class="ghost-btn" @click="clearPdf">关闭预览</button>
          </div>
          <div v-else class="empty-preview">暂无导入内容</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'

const STORAGE_KEY = 'zmg_notebook_notes'
const notes = ref([])
const activeId = ref(null)
const activeTitle = ref('')
const editorRef = ref(null)
const pdfUrl = ref('')

const formatDate = (val) => {
  if (!val) return ''
  const d = new Date(val)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadNotes = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    notes.value = Array.isArray(parsed) ? parsed : []
  } catch {
    notes.value = []
  }
  if (!notes.value.length) createNote()
  if (!activeId.value && notes.value.length) selectNote(notes.value[0].id)
}

const saveNotes = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(notes.value))
}

const createNote = () => {
  const id = `note_${Date.now()}`
  const newNote = {
    id,
    title: '未命名笔记',
    content: '',
    updatedAt: new Date().toISOString()
  }
  notes.value.unshift(newNote)
  activeId.value = id
  activeTitle.value = newNote.title
  nextTick(() => setEditorHtml(''))
  saveNotes()
}

const activeNote = computed(() => notes.value.find(n => n.id === activeId.value))

const selectNote = (id) => {
  activeId.value = id
}

const setEditorHtml = (html) => {
  if (editorRef.value) editorRef.value.innerHTML = html || ''
}

const syncTitle = () => {
  const note = activeNote.value
  if (!note) return
  note.title = activeTitle.value || '未命名笔记'
  note.updatedAt = new Date().toISOString()
  saveNotes()
}

const onEditorInput = () => {
  const note = activeNote.value
  if (!note || !editorRef.value) return
  note.content = editorRef.value.innerHTML
  note.updatedAt = new Date().toISOString()
}

const formatText = (cmd) => {
  document.execCommand(cmd, false, null)
  onEditorInput()
}

const removeNote = () => {
  const note = activeNote.value
  if (!note) return
  notes.value = notes.value.filter(n => n.id !== note.id)
  if (notes.value.length) {
    selectNote(notes.value[0].id)
  } else {
    createNote()
  }
  saveNotes()
}

const onImportFile = async (e) => {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const ext = file.name.toLowerCase().split('.').pop()
  if (ext === 'pdf') {
    if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = URL.createObjectURL(file)
  } else if (ext === 'docx') {
    if (!window.mammoth) {
      alert('Word 解析引擎未加载，请检查 libs 目录')
    } else {
      const arrayBuffer = await file.arrayBuffer()
      const result = await window.mammoth.convertToHtml({ arrayBuffer })
      setEditorHtml(result.value)
      onEditorInput()
    }
  } else {
    alert('仅支持导入 .docx 或 .pdf')
  }
  e.target.value = ''
}

const clearPdf = () => {
  if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
  pdfUrl.value = ''
}

watch(activeId, () => {
  const note = activeNote.value
  activeTitle.value = note?.title || ''
  nextTick(() => setEditorHtml(note?.content || ''))
})

onMounted(loadNotes)
</script>

<style scoped>
.notebook-page {
  display: flex;
  height: 100vh;
  background: #f5f7fb;
  color: #1f2937;
}

.sidebar {
  width: 260px;
  background: #ffffff;
  border-right: 1px solid rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.sidebar-header .title {
  font-weight: 600;
}

.note-list {
  overflow-y: auto;
  padding: 8px;
}

.note-item {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 6px;
  background: transparent;
}

.note-item.active {
  background: rgba(59, 130, 246, 0.12);
  color: #1f6feb;
}

.note-title {
  font-size: 14px;
  font-weight: 500;
}

.note-meta {
  font-size: 11px;
  color: #8b949e;
  margin-top: 4px;
}

.editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.toolbar {
  background: #fff;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-input {
  flex: 1;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 14px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ghost-btn,
.primary-btn,
.danger-btn {
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.primary-btn {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.danger-btn {
  color: #e03131;
  border-color: rgba(224, 49, 49, 0.3);
}

.file-btn input {
  display: none;
}

.editor-body {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
  padding: 12px;
  height: calc(100vh - 60px);
}

.editor-pane,
.preview-pane {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.rich-editor {
  flex: 1;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  padding: 12px;
  outline: none;
  overflow: auto;
  min-height: 300px;
}

.preview-title {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.pdf-preview {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pdf-content {
  width: 100%;
}

.empty-preview {
  color: #9ca3af;
  font-size: 13px;
}

@media (max-width: 900px) {
  .notebook-page {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: 160px;
  }

  .editor-body {
    grid-template-columns: 1fr;
    height: auto;
  }
}
</style>
