<template>
  <section class="page-stack">
    <div>
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">基础数据</p>
            <h3>{{ editingId ? '编辑学期' : '新建学期' }}</h3>
          </div>
          <button v-if="editingId" class="ghost-btn" type="button" @click="resetForm">新建</button>
        </div>

        <form class="form-grid" @submit.prevent="submitForm">
          <label>
            学期名称
            <input v-model.trim="form.name" placeholder="2025-2026-1" required />
            <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
          </label>

          <label>
            开始日期
            <input v-model="form.start_date" type="date" />
            <span v-if="fieldErrors.start_date" class="field-error">{{ fieldErrors.start_date }}</span>
          </label>

          <label>
            结束日期
            <input v-model="form.end_date" type="date" />
            <span v-if="fieldErrors.end_date" class="field-error">{{ fieldErrors.end_date }}</span>
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '保存中...' : editingId ? '更新学期' : '创建学期' }}
            </button>
            <button class="ghost-btn" type="button" @click="resetForm">清空</button>
          </div>
        </form>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>

    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">学期目录</p>
          <h3>已配置学期</h3>
        </div>
        <button class="ghost-btn" :disabled="loading" type="button" @click="loadTerms">刷新</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>开始日期</th>
              <th>结束日期</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in terms" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ formatDate(item.start_date) }}</td>
              <td>{{ formatDate(item.end_date) }}</td>
              <td>{{ formatDateTime(item.updated_at) }}</td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="startEdit(item)">编辑</button>
              </td>
            </tr>
            <tr v-if="!terms.length">
              <td class="table-empty" colspan="6">暂未配置学期。</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          :current-page="currentPage"
          :disabled="loading"
          :page-size="pageSize"
          :total="total"
          background
          layout="total, prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>
    </ExpandablePanel>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import ExpandablePanel from '../../components/ExpandablePanel.vue'
import { createTerm, fetchTerms, normalizeListResponse, updateTerm } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDate, formatDateTime } from '../../utils/formatters'

const terms = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const message = reactive({
  text: '',
  type: 'success',
})

const form = reactive(createEmptyForm())
const fieldErrors = reactive(createEmptyErrors())

function createEmptyForm() {
  return {
    name: '',
    start_date: '',
    end_date: '',
  }
}

function createEmptyErrors() {
  return {
    name: '',
    start_date: '',
    end_date: '',
  }
}

function clearFieldErrors() {
  Object.assign(fieldErrors, createEmptyErrors())
}

function assignForm(payload) {
  Object.assign(form, createEmptyForm(), payload)
}

async function loadTerms() {
  loading.value = true

  try {
    await withPageLoading(async () => {
      const response = await fetchTerms({
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      terms.value = results
      total.value = count
    })
  } catch (error) {
    message.text = error.message || '加载学期列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadTerms()
}

function startEdit(term) {
  editingId.value = term.id
  assignForm({
    name: term.name,
    start_date: term.start_date || '',
    end_date: term.end_date || '',
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

  if (!form.name.trim()) {
    fieldErrors.name = '学期名称不能为空。'
  }

  if (form.start_date && form.end_date && form.end_date < form.start_date) {
    fieldErrors.end_date = '结束日期不能早于开始日期。'
  }

  const hasError = Object.values(fieldErrors).some(Boolean)
  if (hasError) {
    message.text = '请先修正表单错误后再提交。'
    message.type = 'error'
  }

  return !hasError
}

async function submitForm() {
  message.text = ''
  if (!validateForm()) return

  submitting.value = true

  try {
    const payload = {
      name: form.name.trim(),
      start_date: form.start_date || null,
      end_date: form.end_date || null,
    }

    if (editingId.value) {
      await updateTerm(editingId.value, payload)
      message.text = '学期更新成功。'
    } else {
      await createTerm(payload)
      currentPage.value = Math.max(1, Math.ceil((total.value + 1) / pageSize.value))
      message.text = '学期创建成功。'
    }

    message.type = 'success'
    resetForm()
    await loadTerms()
  } catch (error) {
    message.text = error.message || '保存学期失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTerms()
})
</script>

