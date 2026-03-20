<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">基础数据</p>
            <h3>轮次筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadRounds">
          <label>
            学期
            <select v-model="filters.termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">{{ loading ? '加载中...' : '应用' }}</button>
            <button class="ghost-btn" type="button" @click="resetFilters">重置</button>
          </div>
        </form>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">基础数据</p>
            <h3>{{ editingId ? '编辑轮次' : '新建轮次' }}</h3>
          </div>
          <button v-if="editingId" class="ghost-btn" type="button" @click="resetForm">新建</button>
        </div>

        <form class="form-grid" @submit.prevent="submitForm">
          <label>
            学期
            <select v-model="form.term" required>
              <option value="" disabled>请选择学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
            <span v-if="fieldErrors.term" class="field-error">{{ fieldErrors.term }}</span>
          </label>

          <label>
            轮次名称
            <input v-model.trim="form.name" placeholder="第一轮" required />
            <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
          </label>

          <label>
            开始时间
            <input v-model="form.start_at" required type="datetime-local" />
            <span v-if="fieldErrors.start_at" class="field-error">{{ fieldErrors.start_at }}</span>
          </label>

          <label>
            结束时间
            <input v-model="form.end_at" required type="datetime-local" />
            <span v-if="fieldErrors.end_at" class="field-error">{{ fieldErrors.end_at }}</span>
          </label>

          <label>
            适用对象
            <select v-model="form.target_scope">
              <option v-for="item in roundScopeOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>

          <label>
            最大选课数
            <input v-model.number="form.max_courses" min="0" type="number" />
            <span v-if="fieldErrors.max_courses" class="field-error">{{ fieldErrors.max_courses }}</span>
          </label>

          <label class="toggle-field">
            允许退课
            <input v-model="form.allow_drop" type="checkbox" />
          </label>

          <label class="toggle-field">
            启用
            <input v-model="form.enabled" type="checkbox" />
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '保存中...' : editingId ? '更新轮次' : '创建轮次' }}
            </button>
            <button class="ghost-btn" type="button" @click="resetForm">清空</button>
          </div>
        </form>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>
    </div>

    <article class="panel-card table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">轮次目录</p>
          <h3>已配置选课轮次</h3>
        </div>
        <span class="badge badge-neutral">{{ rounds.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>学期</th>
              <th>名称</th>
              <th>时间窗口</th>
              <th>范围</th>
              <th>最大选课数</th>
              <th>退课</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rounds" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.term_name }}</td>
              <td>{{ item.name }}</td>
              <td>{{ formatDateTime(item.start_at) }} 至 {{ formatDateTime(item.end_at) }}</td>
              <td>{{ roundScopeLabel(item.target_scope) }}</td>
              <td>{{ item.max_courses }}</td>
              <td>{{ item.allow_drop ? '允许' : '不允许' }}</td>
              <td>
                <span :class="['badge', item.enabled ? 'badge-on' : 'badge-off']">
                  {{ item.enabled ? '启用' : '停用' }}
                </span>
              </td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="startEdit(item)">编辑</button>
              </td>
            </tr>
            <tr v-if="!rounds.length">
              <td class="table-empty" colspan="9">当前筛选条件下没有轮次数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createRound, fetchRounds, fetchTerms, updateRound } from '../../services/api'
import { formatDateTime, roundScopeOptions, toDateTimeLocal, toIsoDateTime } from '../../utils/formatters'

const terms = ref([])
const rounds = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const filters = reactive({
  termId: '',
})

const message = reactive({
  text: '',
  type: 'success',
})

const form = reactive(createEmptyForm())
const fieldErrors = reactive(createEmptyErrors())

function createEmptyForm() {
  return {
    term: '',
    name: '',
    start_at: '',
    end_at: '',
    target_scope: 'student',
    max_courses: 0,
    allow_drop: true,
    enabled: true,
  }
}

function createEmptyErrors() {
  return {
    term: '',
    name: '',
    start_at: '',
    end_at: '',
    max_courses: '',
  }
}

function clearFieldErrors() {
  Object.assign(fieldErrors, createEmptyErrors())
}

function assignForm(payload) {
  Object.assign(form, createEmptyForm(), payload)
}

function roundScopeLabel(value) {
  return roundScopeOptions.find((item) => item.value === value)?.label || value
}

async function loadBaseData() {
  terms.value = await fetchTerms()
}

async function loadRounds() {
  loading.value = true

  try {
    rounds.value = await fetchRounds({ termId: filters.termId })
  } catch (error) {
    message.text = error.message || '加载轮次列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.termId = ''
  loadRounds()
}

function startEdit(round) {
  editingId.value = round.id
  assignForm({
    term: String(round.term),
    name: round.name,
    start_at: toDateTimeLocal(round.start_at),
    end_at: toDateTimeLocal(round.end_at),
    target_scope: round.target_scope,
    max_courses: round.max_courses,
    allow_drop: round.allow_drop,
    enabled: round.enabled,
  })
  clearFieldErrors()
  message.text = ''
}

function resetForm() {
  editingId.value = null
  assignForm({})
  clearFieldErrors()
  message.text = ''
}

function validateForm() {
  clearFieldErrors()

  if (!form.term) {
    fieldErrors.term = '必须选择学期。'
  }

  if (!form.name.trim()) {
    fieldErrors.name = '轮次名称不能为空。'
  }

  if (!form.start_at) {
    fieldErrors.start_at = '开始时间不能为空。'
  }

  if (!form.end_at) {
    fieldErrors.end_at = '结束时间不能为空。'
  }

  if (Number(form.max_courses) < 0) {
    fieldErrors.max_courses = '最大选课数不能小于 0。'
  }

  if (form.start_at && form.end_at) {
    const startTime = new Date(form.start_at).getTime()
    const endTime = new Date(form.end_at).getTime()
    if (Number.isNaN(startTime) || Number.isNaN(endTime) || endTime <= startTime) {
      fieldErrors.end_at = '结束时间必须晚于开始时间。'
    }
  }

  const hasError = Object.values(fieldErrors).some(Boolean)
  if (hasError) {
    message.text = '请先修正表单错误后再提交。'
    message.type = 'error'
  }

  return !hasError
}

function buildPayload() {
  return {
    term: Number(form.term),
    name: form.name.trim(),
    start_at: toIsoDateTime(form.start_at),
    end_at: toIsoDateTime(form.end_at),
    target_scope: form.target_scope,
    max_courses: Number(form.max_courses || 0),
    allow_drop: form.allow_drop,
    enabled: form.enabled,
  }
}

async function submitForm() {
  message.text = ''
  if (!validateForm()) return

  submitting.value = true

  try {
    if (editingId.value) {
      await updateRound(editingId.value, buildPayload())
      message.text = '轮次更新成功。'
    } else {
      await createRound(buildPayload())
      message.text = '轮次创建成功。'
    }

    message.type = 'success'
    resetForm()
    await loadRounds()
  } catch (error) {
    message.text = error.message || '保存轮次失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    await loadBaseData()
    await loadRounds()
  } catch (error) {
    message.text = error.message || '初始化轮次管理失败。'
    message.type = 'error'
  }
})
</script>
