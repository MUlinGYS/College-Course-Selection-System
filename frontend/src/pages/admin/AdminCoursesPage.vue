<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">课程库</p>
            <h3>课程筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadCourses">
          <label>
            搜索
            <input v-model.trim="filters.q" placeholder="课程编号或课程名称" />
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">{{ loading ? '加载中...' : '查询' }}</button>
            <button class="ghost-btn" type="button" @click="resetFilters">重置</button>
          </div>
        </form>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">课程库</p>
            <h3>{{ editingId ? '编辑课程' : '新建课程' }}</h3>
          </div>
          <button v-if="editingId" class="ghost-btn" type="button" @click="resetForm">新建</button>
        </div>

        <form class="form-grid" @submit.prevent="submitForm">
          <label>
            课程编号
            <input v-model.trim="form.code" placeholder="CS101" required />
            <span v-if="fieldErrors.code" class="field-error">{{ fieldErrors.code }}</span>
          </label>

          <label>
            课程名称
            <input v-model.trim="form.name" placeholder="程序设计基础" required />
            <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
          </label>

          <label>
            学分
            <input v-model.number="form.credits" min="0" type="number" />
            <span v-if="fieldErrors.credits" class="field-error">{{ fieldErrors.credits }}</span>
          </label>

          <label class="span-2">
            课程简介
            <textarea v-model="form.description" placeholder="请输入课程简介"></textarea>
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '保存中...' : editingId ? '更新课程' : '创建课程' }}
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
          <p class="eyebrow">课程目录</p>
          <h3>已配置课程</h3>
        </div>
        <span class="badge badge-neutral">{{ courses.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>编号</th>
              <th>名称</th>
              <th>学分</th>
              <th>简介</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in courses" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.code }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.credits }}</td>
              <td>{{ item.description || '-' }}</td>
              <td>{{ formatDateTime(item.updated_at) }}</td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="startEdit(item)">编辑</button>
                <button class="inline-btn danger" type="button" @click="removeCourse(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!courses.length">
              <td class="table-empty" colspan="7">当前筛选条件下没有课程数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createCourse, deleteCourse, fetchCourses, updateCourse } from '../../services/api'
import { formatDateTime } from '../../utils/formatters'

const courses = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const filters = reactive({
  q: '',
})

const message = reactive({
  text: '',
  type: 'success',
})

const form = reactive(createEmptyForm())
const fieldErrors = reactive(createEmptyErrors())

function createEmptyForm() {
  return {
    code: '',
    name: '',
    credits: 0,
    description: '',
  }
}

function createEmptyErrors() {
  return {
    code: '',
    name: '',
    credits: '',
  }
}

function clearFieldErrors() {
  Object.assign(fieldErrors, createEmptyErrors())
}

function assignForm(payload) {
  Object.assign(form, createEmptyForm(), payload)
}

async function loadCourses() {
  loading.value = true

  try {
    courses.value = await fetchCourses(filters)
  } catch (error) {
    message.text = error.message || '加载课程列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.q = ''
  loadCourses()
}

function startEdit(course) {
  editingId.value = course.id
  assignForm({
    code: course.code,
    name: course.name,
    credits: course.credits,
    description: course.description || '',
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

  if (!form.code.trim()) {
    fieldErrors.code = '课程编号不能为空。'
  }

  if (!form.name.trim()) {
    fieldErrors.name = '课程名称不能为空。'
  }

  if (Number(form.credits) < 0) {
    fieldErrors.credits = '学分不能小于 0。'
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
      code: form.code.trim(),
      name: form.name.trim(),
      credits: Number(form.credits || 0),
      description: form.description.trim(),
    }

    if (editingId.value) {
      await updateCourse(editingId.value, payload)
      message.text = '课程更新成功。'
    } else {
      await createCourse(payload)
      message.text = '课程创建成功。'
    }

    message.type = 'success'
    resetForm()
    await loadCourses()
  } catch (error) {
    message.text = error.message || '保存课程失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

async function removeCourse(course) {
  const accepted = window.confirm(`确认删除课程“${course.code}”吗？`)
  if (!accepted) return

  try {
    await deleteCourse(course.id)
    if (editingId.value === course.id) {
      resetForm()
    }
    message.text = '课程删除成功。'
    message.type = 'success'
    await loadCourses()
  } catch (error) {
    message.text = error.message || '删除课程失败。'
    message.type = 'error'
  }
}

onMounted(() => {
  loadCourses()
})
</script>
