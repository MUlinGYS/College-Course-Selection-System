<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">教学数据</p>
            <h3>班级筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadSections">
          <label>
            学期
            <select v-model="filters.termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <label>
            课程
            <select v-model="filters.courseId">
              <option value="">全部课程</option>
              <option v-for="course in courses" :key="course.id" :value="String(course.id)">
                {{ course.code }} - {{ course.name }}
              </option>
            </select>
          </label>

          <label>
            教师
            <select v-model="filters.teacherId">
              <option value="">全部教师</option>
              <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                {{ teacher.real_name || teacher.username }}
              </option>
            </select>
          </label>

          <label>
            搜索
            <input v-model.trim="filters.q" placeholder="班级名称、教师、地点" />
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
            <p class="eyebrow">教学数据</p>
            <h3>{{ editingId ? '编辑班级' : '新建班级' }}</h3>
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
            课程
            <select v-model="form.course" required>
              <option value="" disabled>请选择课程</option>
              <option v-for="course in courses" :key="course.id" :value="String(course.id)">
                {{ course.code }} - {{ course.name }}
              </option>
            </select>
            <span v-if="fieldErrors.course" class="field-error">{{ fieldErrors.course }}</span>
          </label>

          <label>
            教师
            <select v-model="form.teacher" required>
              <option value="" disabled>请选择教师</option>
              <option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">
                {{ teacher.real_name || teacher.username }}
              </option>
            </select>
            <span v-if="fieldErrors.teacher" class="field-error">{{ fieldErrors.teacher }}</span>
          </label>

          <label>
            班级名称
            <input v-model.trim="form.name" placeholder="1班" required />
            <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
          </label>

          <label>
            容量
            <input v-model.number="form.capacity" min="0" type="number" />
            <span v-if="fieldErrors.capacity" class="field-error">{{ fieldErrors.capacity }}</span>
          </label>

          <label>
            星期
            <select v-model="form.weekday">
              <option v-for="item in weekdayOptions" :key="item.value" :value="String(item.value)">{{ item.label }}</option>
            </select>
          </label>

          <label>
            开始时间
            <input v-model="form.start_time" required type="time" />
            <span v-if="fieldErrors.start_time" class="field-error">{{ fieldErrors.start_time }}</span>
          </label>

          <label>
            结束时间
            <input v-model="form.end_time" required type="time" />
            <span v-if="fieldErrors.end_time" class="field-error">{{ fieldErrors.end_time }}</span>
          </label>

          <label class="span-2">
            地点
            <input v-model.trim="form.location" placeholder="教学楼 A-201" />
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '保存中...' : editingId ? '更新班级' : '创建班级' }}
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
          <p class="eyebrow">班级目录</p>
          <h3>已配置开课班级</h3>
        </div>
        <span class="badge badge-neutral">{{ sections.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>学期</th>
              <th>课程</th>
              <th>班级</th>
              <th>教师</th>
              <th>上课时间</th>
              <th>容量</th>
              <th>地点</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sections" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.term_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.teacher_name }}</td>
              <td>{{ joinSectionSchedule(item) }}</td>
              <td>{{ item.capacity }}</td>
              <td>{{ item.location || '-' }}</td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="startEdit(item)">编辑</button>
                <button class="inline-btn danger" type="button" @click="removeSection(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!sections.length">
              <td class="table-empty" colspan="9">当前筛选条件下没有班级数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import {
  createSection,
  deleteSection,
  fetchCourses,
  fetchSections,
  fetchTerms,
  fetchUsers,
  updateSection,
} from '../../services/api'
import { joinSectionSchedule, weekdayOptions } from '../../utils/formatters'

const terms = ref([])
const courses = ref([])
const teachers = ref([])
const sections = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const filters = reactive({
  termId: '',
  courseId: '',
  teacherId: '',
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
    term: '',
    course: '',
    teacher: '',
    name: '',
    capacity: 0,
    weekday: '1',
    start_time: '08:00',
    end_time: '09:40',
    location: '',
  }
}

function createEmptyErrors() {
  return {
    term: '',
    course: '',
    teacher: '',
    name: '',
    capacity: '',
    start_time: '',
    end_time: '',
  }
}

function clearFieldErrors() {
  Object.assign(fieldErrors, createEmptyErrors())
}

function assignForm(payload) {
  Object.assign(form, createEmptyForm(), payload)
}

async function loadBaseData() {
  const [termList, courseList, teacherList] = await Promise.all([
    fetchTerms(),
    fetchCourses(),
    fetchUsers({ role: 'teacher' }),
  ])

  terms.value = termList
  courses.value = courseList
  teachers.value = teacherList
}

async function loadSections() {
  loading.value = true

  try {
    sections.value = await fetchSections(filters)
  } catch (error) {
    message.text = error.message || '加载班级列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.termId = ''
  filters.courseId = ''
  filters.teacherId = ''
  filters.q = ''
  loadSections()
}

function startEdit(section) {
  editingId.value = section.id
  assignForm({
    term: String(section.term),
    course: String(section.course),
    teacher: String(section.teacher),
    name: section.name,
    capacity: section.capacity,
    weekday: String(section.weekday),
    start_time: section.start_time?.slice(0, 5) || '08:00',
    end_time: section.end_time?.slice(0, 5) || '09:40',
    location: section.location || '',
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

  if (!form.course) {
    fieldErrors.course = '必须选择课程。'
  }

  if (!form.teacher) {
    fieldErrors.teacher = '必须选择教师。'
  }

  if (!form.name.trim()) {
    fieldErrors.name = '班级名称不能为空。'
  }

  if (Number(form.capacity) < 0) {
    fieldErrors.capacity = '容量不能小于 0。'
  }

  if (!form.start_time) {
    fieldErrors.start_time = '开始时间不能为空。'
  }

  if (!form.end_time) {
    fieldErrors.end_time = '结束时间不能为空。'
  }

  if (form.start_time && form.end_time && form.end_time <= form.start_time) {
    fieldErrors.end_time = '结束时间必须晚于开始时间。'
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
    course: Number(form.course),
    teacher: Number(form.teacher),
    name: form.name.trim(),
    capacity: Number(form.capacity || 0),
    weekday: Number(form.weekday),
    start_time: form.start_time,
    end_time: form.end_time,
    location: form.location.trim(),
  }
}

async function submitForm() {
  message.text = ''
  if (!validateForm()) return

  submitting.value = true

  try {
    if (editingId.value) {
      await updateSection(editingId.value, buildPayload())
      message.text = '班级更新成功。'
    } else {
      await createSection(buildPayload())
      message.text = '班级创建成功。'
    }

    message.type = 'success'
    resetForm()
    await loadSections()
  } catch (error) {
    message.text = error.message || '保存班级失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

async function removeSection(section) {
  const accepted = window.confirm(`确认删除班级“${section.course_code} - ${section.name}”吗？`)
  if (!accepted) return

  try {
    await deleteSection(section.id)
    if (editingId.value === section.id) {
      resetForm()
    }
    message.text = '班级删除成功。'
    message.type = 'success'
    await loadSections()
  } catch (error) {
    message.text = error.message || '删除班级失败。'
    message.type = 'error'
  }
}

onMounted(async () => {
  try {
    await loadBaseData()
    await loadSections()
  } catch (error) {
    message.text = error.message || '初始化班级管理失败。'
    message.type = 'error'
  }
})
</script>
