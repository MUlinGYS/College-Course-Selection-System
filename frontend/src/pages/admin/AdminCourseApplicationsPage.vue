<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">申报审核</p>
            <h3>筛选条件</h3>
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
              <option v-for="item in filterRounds" :key="item.id" :value="String(item.id)">{{ item.name }}</option>
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
            <input v-model.trim="filters.q" placeholder="教师、课程编号、课程名称、班级名称" />
          </label>

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
            <p class="eyebrow">申报审核</p>
            <h3>审核面板</h3>
          </div>
        </div>

        <template v-if="selectedApplication">
          <div class="stats-strip">
            <div class="stat-box">
              <span class="stat-label">当前筛选记录</span>
              <strong>{{ total }}</strong>
            </div>
            <div class="stat-box">
              <span class="stat-label">当前状态</span>
              <strong>{{ courseApplicationStatusLabel(selectedApplication.status) }}</strong>
            </div>
            <div class="stat-box">
              <span class="stat-label">申报教师</span>
              <strong>{{ selectedApplication.teacher_name }}</strong>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">学期</span>
              <strong>{{ selectedApplication.term_name }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">轮次</span>
              <strong>{{ selectedApplication.round_name }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">课程编号</span>
              <strong>{{ selectedApplication.course_code }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">课程名称</span>
              <strong>{{ selectedApplication.course_name }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">班级名称</span>
              <strong>{{ selectedApplication.section_name }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">地点 / 容量</span>
              <strong>{{ selectedApplication.location || '-' }} / {{ selectedApplication.capacity }}</strong>
            </div>
            <div class="detail-item span-2">
              <span class="detail-label">上课时间</span>
              <strong>
                {{ weekdayLabel(selectedApplication.weekday) }}
                {{ formatTime(selectedApplication.start_time) }}-{{ formatTime(selectedApplication.end_time) }}
              </strong>
            </div>
            <div class="detail-item span-2">
              <span class="detail-label">课程简介</span>
              <strong>{{ selectedApplication.course_description || '-' }}</strong>
            </div>
            <div class="detail-item span-2">
              <span class="detail-label">申报说明</span>
              <strong>{{ selectedApplication.apply_note || '-' }}</strong>
            </div>
          </div>

          <label class="single-column" style="margin-top: 14px">
            审核意见
            <textarea
              v-model="reviewForm.review_note"
              :disabled="reviewing"
              placeholder="通过时可选填，驳回时必须填写"
            />
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="reviewing" type="button" @click="submitReview('approve')">
              {{ reviewing ? '处理中...' : '审核通过' }}
            </button>
            <button class="inline-btn danger" :disabled="reviewing" type="button" @click="submitReview('reject')">
              驳回申报
            </button>
          </div>
        </template>

        <p v-else class="muted">当前没有待审核记录，或尚未选择待审核申报。</p>
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">申报列表</p>
          <h3>开课申报记录</h3>
        </div>
        <span class="badge badge-neutral">共 {{ total }} 条</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>教师</th>
              <th>学期</th>
              <th>轮次</th>
              <th>课程</th>
              <th>班级</th>
              <th>上课时间</th>
              <th>状态</th>
              <th>提交时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in applications" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.teacher_name }}</td>
              <td>{{ item.term_name }}</td>
              <td>{{ item.round_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.section_name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>
                <span :class="['badge', applicationBadgeClass(item.status)]">
                  {{ courseApplicationStatusLabel(item.status) }}
                </span>
              </td>
              <td>{{ formatDateTime(item.created_at) }}</td>
              <td class="actions">
                <button class="inline-btn" type="button" @click="handleRowAction(item)">
                  {{ item.status === 'pending' ? '审核' : '查看' }}
                </button>
              </td>
            </tr>
            <tr v-if="!applications.length">
              <td class="table-empty" colspan="10">当前筛选条件下没有申报记录。</td>
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

    <el-dialog v-model="detailDialogVisible" title="申报详情" width="720px">
      <template v-if="detailApplication">
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">状态</span>
            <strong>{{ courseApplicationStatusLabel(detailApplication.status) }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">申报教师</span>
            <strong>{{ detailApplication.teacher_name }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">学期</span>
            <strong>{{ detailApplication.term_name }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">轮次</span>
            <strong>{{ detailApplication.round_name }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">课程编号</span>
            <strong>{{ detailApplication.course_code }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">课程名称</span>
            <strong>{{ detailApplication.course_name }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">班级名称</span>
            <strong>{{ detailApplication.section_name }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">地点 / 容量</span>
            <strong>{{ detailApplication.location || '-' }} / {{ detailApplication.capacity }}</strong>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">上课时间</span>
            <strong>
              {{ weekdayLabel(detailApplication.weekday) }}
              {{ formatTime(detailApplication.start_time) }}-{{ formatTime(detailApplication.end_time) }}
            </strong>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">课程简介</span>
            <strong>{{ detailApplication.course_description || '-' }}</strong>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">申报说明</span>
            <strong>{{ detailApplication.apply_note || '-' }}</strong>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">审核意见</span>
            <strong>{{ detailApplication.review_note || '-' }}</strong>
          </div>
          <div v-if="detailApplication.linked_section_name" class="detail-item span-2">
            <span class="detail-label">已生成开课班级</span>
            <strong>
              {{ detailApplication.linked_course_code || detailApplication.course_code }}
              -
              {{ detailApplication.linked_section_name }}
            </strong>
          </div>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import ExpandablePanel from '../../components/ExpandablePanel.vue'
import {
  fetchAdminCourseApplications,
  fetchRounds,
  fetchTerms,
  fetchUsers,
  normalizeListResponse,
  reviewCourseApplication,
} from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import {
  courseApplicationStatusLabel,
  courseApplicationStatusOptions,
  formatDateTime,
  formatTime,
  weekdayLabel,
} from '../../utils/formatters'

const terms = ref([])
const rounds = ref([])
const teachers = ref([])
const applications = ref([])
const loading = ref(false)
const reviewing = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const selectedId = ref(null)
const detailDialogVisible = ref(false)
const detailApplication = ref(null)

const filters = reactive({
  termId: '',
  roundId: '',
  teacherId: '',
  status: '',
  q: '',
})

const reviewForm = reactive({
  review_note: '',
})

const message = reactive({
  text: '',
  type: 'success',
})

const filterRounds = computed(() =>
  filters.termId ? rounds.value.filter((item) => String(item.term) === filters.termId) : rounds.value,
)
const pendingApplications = computed(() => applications.value.filter((item) => item.status === 'pending'))
const selectedApplication = computed(() =>
  pendingApplications.value.find((item) => item.id === selectedId.value) || null,
)

function applicationBadgeClass(status) {
  if (status === 'approved') return 'badge-on'
  if (status === 'rejected') return 'badge-off'
  return 'badge-neutral'
}

async function loadBaseData() {
  const [termList, roundList, teacherList] = await withPageLoading(async () =>
    Promise.all([fetchTerms(), fetchRounds(), fetchUsers({ role: 'teacher' })]),
  )

  terms.value = termList
  rounds.value = roundList
  teachers.value = teacherList
}

function syncSelectedApplication() {
  if (!pendingApplications.value.length) {
    selectedId.value = null
    reviewForm.review_note = ''
    return
  }

  const matched = pendingApplications.value.find((item) => item.id === selectedId.value)
  if (matched) {
    reviewForm.review_note = ''
    return
  }

  selectedId.value = pendingApplications.value[0].id
  reviewForm.review_note = ''
}

async function loadApplications() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const response = await fetchAdminCourseApplications({
        ...filters,
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      applications.value = results
      total.value = count
      syncSelectedApplication()
    })
  } catch (error) {
    message.text = error.message || '加载申报审核列表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function handleRowAction(item) {
  if (item.status === 'pending') {
    selectedId.value = item.id
    reviewForm.review_note = ''
    return
  }

  detailApplication.value = item
  detailDialogVisible.value = true
}

async function submitReview(action) {
  if (!selectedApplication.value) return

  reviewing.value = true

  try {
    await reviewCourseApplication(selectedApplication.value.id, {
      action,
      review_note: reviewForm.review_note.trim(),
    })
    message.text = action === 'approve' ? '申报审核通过，已生成开课班级。' : '申报已驳回。'
    message.type = 'success'
    await loadApplications()
  } catch (error) {
    message.text = error.message || '审核申报失败。'
    message.type = 'error'
  } finally {
    reviewing.value = false
  }
}

async function handleSearch() {
  currentPage.value = 1
  await loadApplications()
}

function resetFilters() {
  filters.termId = ''
  filters.roundId = ''
  filters.teacherId = ''
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

onMounted(async () => {
  try {
    await loadBaseData()
    await loadApplications()
  } catch (error) {
    message.text = error.message || '初始化申报审核页面失败。'
    message.type = 'error'
  }
})
</script>
