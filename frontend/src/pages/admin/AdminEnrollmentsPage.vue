<template>
  <section class="page-stack">
    <div class="panel-grid admin-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">选课查询</p>
            <h3>查询条件</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="handleSearch">
          <label>
            轮次
            <select v-model="filters.roundId">
              <option value="">全部轮次</option>
              <option v-for="item in rounds" :key="item.id" :value="String(item.id)">
                {{ item.term_name }} - {{ item.name }}
              </option>
            </select>
          </label>

          <label>
            班级
            <select v-model="filters.sectionId">
              <option value="">全部班级</option>
              <option v-for="item in sections" :key="item.id" :value="String(item.id)">
                {{ item.course_code }} - {{ item.name }}
              </option>
            </select>
          </label>

          <label>
            学生
            <select v-model="filters.studentId">
              <option value="">全部学生</option>
              <option v-for="item in students" :key="item.id" :value="String(item.id)">
                {{ item.real_name || item.username }}
              </option>
            </select>
          </label>

          <label>
            状态
            <select v-model="filters.status">
              <option value="">全部状态</option>
              <option v-for="item in enrollmentStatusOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
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
            <p class="eyebrow">数据概览</p>
            <h3>记录概览</h3>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-box">
            <span class="stat-label">记录总数</span>
            <strong>{{ total }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">已选记录</span>
            <strong>{{ enrolledCount }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">已退记录</span>
            <strong>{{ droppedCount }}</strong>
          </div>
        </div>
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">选课记录目录</p>
          <h3>选课记录</h3>
        </div>
        <span class="badge badge-neutral">共 {{ total }} 条</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>学生</th>
              <th>轮次</th>
              <th>学期</th>
              <th>课程</th>
              <th>班级</th>
              <th>教师</th>
              <th>上课时间</th>
              <th>状态</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in enrollments" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.student_name }}（{{ item.student_username }}）</td>
              <td>{{ item.round_name }}</td>
              <td>{{ item.term_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.section_name }}</td>
              <td>{{ item.teacher_name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>
                <span :class="['badge', item.status === 'enrolled' ? 'badge-on' : 'badge-off']">
                  {{ enrollmentStatusLabel(item.status) }}
                </span>
              </td>
              <td>{{ formatDateTime(item.created_at) }}</td>
            </tr>
            <tr v-if="!enrollments.length">
              <td class="table-empty" colspan="10">当前筛选条件下没有选课记录。</td>
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
import { computed, onMounted, reactive, ref } from 'vue'

import ExpandablePanel from '../../components/ExpandablePanel.vue'
import { fetchEnrollmentRecords, fetchRounds, fetchSections, fetchUsers, normalizeListResponse } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import {
  enrollmentStatusLabel,
  enrollmentStatusOptions,
  formatDateTime,
  formatTime,
  weekdayLabel,
} from '../../utils/formatters'

const rounds = ref([])
const sections = ref([])
const students = ref([])
const enrollments = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const filters = reactive({
  roundId: '',
  sectionId: '',
  studentId: '',
  status: '',
})

const message = reactive({
  text: '',
  type: 'success',
})

const enrolledCount = computed(() => enrollments.value.filter((item) => item.status === 'enrolled').length)
const droppedCount = computed(() => enrollments.value.filter((item) => item.status === 'dropped').length)

async function loadBaseData() {
  const [roundList, sectionList, studentList] = await withPageLoading(async () =>
    Promise.all([fetchRounds(), fetchSections(), fetchUsers({ role: 'student' })]),
  )

  rounds.value = roundList
  sections.value = sectionList
  students.value = studentList
}

async function loadEnrollments() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const response = await fetchEnrollmentRecords({
        ...filters,
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      enrollments.value = results
      total.value = count
    })
  } catch (error) {
    message.text = error.message || '加载选课记录失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  currentPage.value = 1
  await loadEnrollments()
}

function resetFilters() {
  filters.roundId = ''
  filters.sectionId = ''
  filters.studentId = ''
  filters.status = ''
  currentPage.value = 1
  loadEnrollments()
}

function handlePageChange(page) {
  currentPage.value = page
  loadEnrollments()
}

onMounted(async () => {
  try {
    await loadBaseData()
    await loadEnrollments()
  } catch (error) {
    message.text = error.message || '初始化选课记录页失败。'
    message.type = 'error'
  }
})
</script>

