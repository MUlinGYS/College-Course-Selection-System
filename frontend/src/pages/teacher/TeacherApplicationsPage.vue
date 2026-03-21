<template>
  <section class="page-stack">
    <div class="panel-grid teacher-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">教师端</p>
            <h3>申报筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="handleSearch">
          <label>
            学期
            <select v-model="filters.termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <label>
            轮次
            <select v-model="filters.roundId" :disabled="!filterRounds.length">
              <option value="">{{ filterRounds.length ? '全部轮次' : '无轮次' }}</option>
              <option v-for="item in filterRounds" :key="item.id" :value="String(item.id)">
                {{ item.name }}
              </option>
            </select>
          </label>

          <label>
            状态
            <select v-model="filters.status">
              <option value="">全部状态</option>
              <option v-for="item in courseApplicationStatusOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </label>

          <label>
            搜索
            <input v-model.trim="filters.q" placeholder="课程编号、课程名称、班级名称" />
          </label>

          <div class="stats-strip">
            <div class="stat-box">
              <span class="stat-label">记录总数</span>
              <strong>{{ total }}</strong>
            </div>
            <div class="stat-box">
              <span class="stat-label">当前页待审</span>
              <strong>{{ pendingCount }}</strong>
            </div>
            <div class="stat-box">
              <span class="stat-label">当前页通过</span>
              <strong>{{ approvedCount }}</strong>
            </div>
          </div>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">应用筛选</button>
            <button class="ghost-btn" type="button" @click="resetFilters">重置</button>
          </div>
        </form>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">教师端</p>
            <h3>{{ editingId ? (resubmittingRejected ? '重新提交开课申报' : '编辑开课申报') : '新建开课申报' }}</h3>
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
            轮次
            <select v-model="form.round" :disabled="!formRounds.length" required>
              <option value="" disabled>{{ formRounds.length ? '请选择轮次' : '无轮次' }}</option>
              <option v-for="item in formRounds" :key="item.id" :value="String(item.id)">{{ item.name }}</option>
            </select>
            <span v-if="fieldErrors.round" class="field-error">{{ fieldErrors.round }}</span>
          </label>

          <label>
            课程编号
            <input v-model.trim="form.course_code" placeholder="CS101" required />
            <span v-if="fieldErrors.course_code" class="field-error">{{ fieldErrors.course_code }}</span>
          </label>

          <label>
            课程名称
            <input v-model.trim="form.course_name" placeholder="程序设计基础" required />
            <span v-if="fieldErrors.course_name" class="field-error">{{ fieldErrors.course_name }}</span>
          </label>

          <label>
            学分
            <input v-model.number="form.credits" min="0" type="number" />
            <span v-if="fieldErrors.credits" class="field-error">{{ fieldErrors.credits }}</span>
          </label>

          <label>
            班级名称
            <input v-model.trim="form.section_name" placeholder="1班" required />
            <span v-if="fieldErrors.section_name" class="field-error">{{ fieldErrors.section_name }}</span>
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

          <label class="span-2">
            课程简介
            <textarea v-model="form.course_description" placeholder="填写课程简介，便于管理员审核" />
          </label>

          <label class="span-2">
            申报说明
            <textarea v-model="form.apply_note" placeholder="填写本次开课安排、教学对象或审核备注" />
          </label>

          <div class="toolbar span-2">
            <button class="primary-btn" :disabled="submitting" type="submit">
              {{ submitting ? '提交中...' : editingId ? (resubmittingRejected ? '重新提交申报' : '更新申报') : '提交申报' }}
            </button>
            <button class="ghost-btn" type="button" @click="resetForm">清空</button>
          </div>
        </form>
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">申报目录</p>
          <h3>我的开课申报</h3>
        </div>
        <span class="badge badge-neutral">共 {{ total }} 条</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>学期</th>
              <th>轮次</th>
              <th>课程</th>
              <th>班级</th>
              <th>上课时间</th>
              <th>容量</th>
              <th>状态</th>
              <th>审核意见</th>
              <th>提交时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in applications" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.term_name }}</td>
              <td>{{ item.round_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.section_name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>{{ item.capacity }}</td>
              <td>
                <span :class="['badge', applicationBadgeClass(item.status)]">
                  {{ courseApplicationStatusLabel(item.status) }}
                </span>
              </td>
              <td>{{ item.review_note || '-' }}</td>
              <td>{{ formatDateTime(item.created_at) }}</td>
              <td class="actions">
                <button class="inline-btn" :disabled="item.status !== 'pending'" type="button" @click="startEdit(item)">
                  编辑
                </button>
                <button
                  class="inline-btn danger"
                  :disabled="item.status !== 'pending'"
                  type="button"
                  @click="removeApplication(item)"
                >
                  删除
                </button>
                <button
                  v-if="item.status === 'rejected'"
                  class="inline-btn"
                  type="button"
                  @click="resubmitApplication(item)"
                >
                  重新提交
                </button>
              </td>
            </tr>
            <tr v-if="!applications.length">
              <td class="table-empty" colspan="11">当前筛选条件下没有申报记录。</td>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'

import ExpandablePanel from '../../components/ExpandablePanel.vue'
import {
  createTeacherCourseApplication,
  deleteTeacherCourseApplication,
  fetchRounds,
  fetchTeacherCourseApplications,
  fetchTerms,
  normalizeListResponse,
  updateTeacherCourseApplication,
} from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import {
  courseApplicationStatusLabel,
  courseApplicationStatusOptions,
  formatDateTime,
  formatTime,
  weekdayLabel,
  weekdayOptions,
} from '../../utils/formatters'

const terms = ref([])
const rounds = ref([])
const applications = ref([])
const loading = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const resubmittingRejected = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const filters = reactive({
  termId: '',
  roundId: '',
  status: '',
  q: '',
})

const form = reactive(createEmptyForm())
const fieldErrors = reactive(createEmptyErrors())
const message = reactive({
  text: '',
  type: 'success',
})

const filterRounds = computed(() =>
  filters.termId ? rounds.value.filter((item) => String(item.term) === filters.termId) : rounds.value,
)
const formRounds = computed(() =>
  form.term ? rounds.value.filter((item) => String(item.term) === form.term) : [],
)
const pendingCount = computed(() => applications.value.filter((item) => item.status === 'pending').length)
const approvedCount = computed(() => applications.value.filter((item) => item.status === 'approved').length)

function createEmptyForm() {
  return {
    term: '',
    round: '',
    course_code: '',
    course_name: '',
    credits: 0,
    course_description: '',
    section_name: '',
    capacity: 30,
    weekday: '1',
    start_time: '08:00',
    end_time: '09:40',
    location: '',
    apply_note: '',
  }
}

function createEmptyErrors() {
  return {
    term: '',
    round: '',
    course_code: '',
    course_name: '',
    credits: '',
    section_name: '',
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

function applicationBadgeClass(status) {
  if (status === 'approved') return 'badge-on'
  if (status === 'rejected') return 'badge-off'
  return 'badge-neutral'
}

async function loadBaseData() {
  const [termList, roundList] = await withPageLoading(async () =>
    Promise.all([fetchTerms(), fetchRounds()]),
  )
  terms.value = termList
  rounds.value = roundList
}

async function loadApplications() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const response = await fetchTeacherCourseApplications({
        ...filters,
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      applications.value = results
      total.value = count
    })
  } catch (error) {
    message.text = error.message || '加载开课申报失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function validateForm() {
  clearFieldErrors()

  if (!form.term) fieldErrors.term = '必须选择学期。'
  if (!form.round) fieldErrors.round = '必须选择轮次。'
  if (!form.course_code.trim()) fieldErrors.course_code = '课程编号不能为空。'
  if (!form.course_name.trim()) fieldErrors.course_name = '课程名称不能为空。'
  if (!form.section_name.trim()) fieldErrors.section_name = '班级名称不能为空。'
  if (Number(form.credits) < 0) fieldErrors.credits = '学分不能小于 0。'
  if (Number(form.capacity) < 0) fieldErrors.capacity = '容量不能小于 0。'
  if (!form.start_time) fieldErrors.start_time = '开始时间不能为空。'
  if (!form.end_time) fieldErrors.end_time = '结束时间不能为空。'
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
    round: Number(form.round),
    course_code: form.course_code.trim().toUpperCase(),
    course_name: form.course_name.trim(),
    credits: Number(form.credits || 0),
    course_description: form.course_description.trim(),
    section_name: form.section_name.trim(),
    capacity: Number(form.capacity || 0),
    weekday: Number(form.weekday),
    start_time: form.start_time,
    end_time: form.end_time,
    location: form.location.trim(),
    apply_note: form.apply_note.trim(),
  }
}

async function submitForm() {
  message.text = ''
  if (!validateForm()) return

  submitting.value = true

  try {
    if (editingId.value) {
      await updateTeacherCourseApplication(editingId.value, buildPayload())
      message.text = resubmittingRejected.value ? '申报已重新提交。' : '申报更新成功。'
    } else {
      await createTeacherCourseApplication(buildPayload())
      currentPage.value = 1
      message.text = '申报提交成功。'
    }

    message.type = 'success'
    resetForm()
    await loadApplications()
  } catch (error) {
    message.text = error.message || '保存开课申报失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

function fillFormFromApplication(item) {
  assignForm({
    term: String(item.term),
    round: String(item.round),
    course_code: item.course_code || '',
    course_name: item.course_name || '',
    credits: item.credits ?? 0,
    course_description: item.course_description || '',
    section_name: item.section_name || '',
    capacity: item.capacity ?? 0,
    weekday: String(item.weekday),
    start_time: item.start_time?.slice(0, 5) || '08:00',
    end_time: item.end_time?.slice(0, 5) || '09:40',
    location: item.location || '',
    apply_note: item.apply_note || '',
  })
  clearFieldErrors()
}

function startEdit(item) {
  if (item.status !== 'pending') return

  editingId.value = item.id
  resubmittingRejected.value = false
  fillFormFromApplication(item)
  message.text = ''
}

function resetForm() {
  editingId.value = null
  resubmittingRejected.value = false
  assignForm({})
  clearFieldErrors()
}

function resubmitApplication(item) {
  if (item.status !== 'rejected') return

  editingId.value = item.id
  resubmittingRejected.value = true
  fillFormFromApplication(item)
  message.text = '已载入驳回记录，提交后将复用原记录重新进入待审核。'
  message.type = 'success'
}

async function removeApplication(item) {
  if (item.status !== 'pending') return

  const accepted = window.confirm(`确认删除申报“${item.course_code} - ${item.section_name}”吗？`)
  if (!accepted) return

  try {
    await deleteTeacherCourseApplication(item.id)
    if (editingId.value === item.id) {
      resetForm()
    }
    if (applications.value.length === 1 && currentPage.value > 1) {
      currentPage.value -= 1
    }
    message.text = '申报删除成功。'
    message.type = 'success'
    await loadApplications()
  } catch (error) {
    message.text = error.message || '删除开课申报失败。'
    message.type = 'error'
  }
}

async function handleSearch() {
  currentPage.value = 1
  await loadApplications()
}

function resetFilters() {
  filters.termId = ''
  filters.roundId = ''
  filters.status = ''
  filters.q = ''
  currentPage.value = 1
  loadApplications()
}

function handlePageChange(page) {
  currentPage.value = page
  loadApplications()
}

watch(
  () => filters.termId,
  () => {
    if (!filterRounds.value.some((item) => String(item.id) === filters.roundId)) {
      filters.roundId = ''
    }
  },
)

watch(
  () => form.term,
  () => {
    if (!formRounds.value.some((item) => String(item.id) === form.round)) {
      form.round = ''
    }
  },
)

onMounted(async () => {
  try {
    await loadBaseData()
    await loadApplications()
  } catch (error) {
    message.text = error.message || '初始化开课申报页面失败。'
    message.type = 'error'
  }
})
</script>
