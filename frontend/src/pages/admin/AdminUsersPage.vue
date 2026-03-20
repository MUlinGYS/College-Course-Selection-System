<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">管理员</p>
            <h3>用户筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadUsers">
          <label>
            搜索
            <input v-model.trim="filters.q" placeholder="用户名、邮箱、姓名、学号工号、部门" />
          </label>

          <label>
            角色
            <select v-model="filters.role">
              <option value="">全部角色</option>
              <option v-for="item in roleOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">查询</button>
            <button class="ghost-btn" type="button" @click="resetFilters">重置</button>
          </div>
        </form>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">管理员</p>
            <h3>{{ editingId ? '编辑用户' : '新建用户' }}</h3>
          </div>
          <button v-if="editingId" class="ghost-btn" type="button" @click="resetForm">新建</button>
        </div>

        <form class="form-grid" @submit.prevent="submitForm">
          <label>
            用户名
            <input v-model.trim="form.username" required />
            <span v-if="fieldErrors.username" class="field-error">{{ fieldErrors.username }}</span>
          </label>

          <label>
            邮箱
            <input v-model.trim="form.email" type="email" />
          </label>

          <label>
            角色
            <select v-model="form.role" required>
              <option v-for="item in roleOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>

          <label>
            姓名
            <input v-model.trim="form.real_name" />
          </label>

          <label>
            学号
            <input v-model.trim="form.student_no" />
            <span class="field-hint">学生填写学号，教师角色应留空。</span>
            <span v-if="fieldErrors.student_no" class="field-error">{{ fieldErrors.student_no }}</span>
          </label>

          <label>
            工号
            <input v-model.trim="form.teacher_no" />
            <span class="field-hint">教师填写工号，学生角色应留空。</span>
            <span v-if="fieldErrors.teacher_no" class="field-error">{{ fieldErrors.teacher_no }}</span>
          </label>

          <label>
            手机号
            <input v-model.trim="form.phone" />
          </label>

          <label>
            部门
            <input v-model.trim="form.department" />
          </label>

          <label>
            密码
            <input v-model="form.password" :placeholder="editingId ? '留空表示保持原密码' : '至少 6 位'" type="password" />
            <span v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</span>
          </label>

          <label class="toggle-field">
            启用
            <input v-model="form.is_enabled" type="checkbox" />
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '保存中...' : editingId ? '更新用户' : '创建用户' }}
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
          <p class="eyebrow">用户目录</p>
          <h3>用户列表</h3>
        </div>
        <span class="badge badge-neutral">{{ users.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>姓名</th>
              <th>角色</th>
              <th>邮箱</th>
              <th>部门</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in users" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.username }}</td>
              <td>{{ item.real_name || '-' }}</td>
              <td>{{ roleLabel(item.role) }}</td>
              <td>{{ item.email || '-' }}</td>
              <td>{{ item.department || '-' }}</td>
              <td>
                <span :class="['badge', item.is_enabled ? 'badge-on' : 'badge-off']">
                  {{ item.is_enabled ? '启用' : '停用' }}
                </span>
              </td>
              <td>{{ formatDateTime(item.date_joined) }}</td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="startEdit(item)">编辑</button>
                <button class="inline-btn danger" type="button" @click="removeUser(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!users.length">
              <td class="table-empty" colspan="9">当前筛选条件下没有用户数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createUser, deleteUser, fetchUsers, updateUser } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDateTime, roleLabel, roleOptions } from '../../utils/formatters'

const users = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const filters = reactive({
  role: '',
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
    username: '',
    email: '',
    role: 'student',
    real_name: '',
    student_no: '',
    teacher_no: '',
    phone: '',
    department: '',
    password: '',
    is_enabled: true,
  }
}

function createEmptyErrors() {
  return {
    username: '',
    password: '',
    student_no: '',
    teacher_no: '',
  }
}

function clearFieldErrors() {
  Object.assign(fieldErrors, createEmptyErrors())
}

function assignForm(payload) {
  Object.assign(form, createEmptyForm(), payload)
}

async function loadUsers() {
  loading.value = true

  try {
    await withPageLoading(async () => {
      users.value = await fetchUsers(filters)
    })
  } catch (error) {
    message.text = error.message || '加载用户列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.role = ''
  filters.q = ''
  loadUsers()
}

function resetForm() {
  editingId.value = null
  assignForm({})
  clearFieldErrors()
  message.text = ''
}

function startEdit(user) {
  editingId.value = user.id
  assignForm({
    username: user.username,
    email: user.email || '',
    role: user.role || 'student',
    real_name: user.real_name || '',
    student_no: user.student_no || '',
    teacher_no: user.teacher_no || '',
    phone: user.phone || '',
    department: user.department || '',
    password: '',
    is_enabled: user.is_enabled,
  })
  clearFieldErrors()
  message.text = ''
}

function validateForm() {
  clearFieldErrors()

  if (!form.username.trim()) {
    fieldErrors.username = '用户名不能为空。'
  }

  if (!editingId.value && !form.password) {
    fieldErrors.password = '创建用户时必须填写密码。'
  } else if (form.password && form.password.length < 6) {
    fieldErrors.password = '密码长度不能少于 6 位。'
  }

  if (form.role === 'student' && form.teacher_no.trim()) {
    fieldErrors.teacher_no = '学生角色不能填写工号。'
  }

  if (form.role === 'teacher' && form.student_no.trim()) {
    fieldErrors.student_no = '教师角色不能填写学号。'
  }

  const hasError = Object.values(fieldErrors).some(Boolean)
  if (hasError) {
    message.text = '请先修正表单错误后再提交。'
    message.type = 'error'
  }

  return !hasError
}

function buildPayload() {
  const payload = {
    username: form.username.trim(),
    email: form.email.trim(),
    role: form.role,
    real_name: form.real_name.trim(),
    student_no: form.student_no.trim(),
    teacher_no: form.teacher_no.trim(),
    phone: form.phone.trim(),
    department: form.department.trim(),
    is_enabled: form.is_enabled,
  }

  if (form.password) {
    payload.password = form.password
  }

  return payload
}

async function submitForm() {
  message.text = ''
  if (!validateForm()) return

  submitting.value = true

  try {
    if (editingId.value) {
      await updateUser(editingId.value, buildPayload())
      message.text = '用户更新成功。'
    } else {
      await createUser(buildPayload())
      message.text = '用户创建成功。'
    }

    message.type = 'success'
    resetForm()
    await loadUsers()
  } catch (error) {
    message.text = error.message || '保存用户失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

async function removeUser(user) {
  const accepted = window.confirm(`确认删除用户“${user.username}”吗？`)
  if (!accepted) return

  message.text = ''

  try {
    await deleteUser(user.id)
    if (editingId.value === user.id) {
      resetForm()
    }
    message.text = '用户删除成功。'
    message.type = 'success'
    await loadUsers()
  } catch (error) {
    message.text = error.message || '删除用户失败。'
    message.type = 'error'
  }
}

onMounted(() => {
  loadUsers()
})
</script>
