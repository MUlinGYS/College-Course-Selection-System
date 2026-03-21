<template>
  <section class="page-stack">
    <div class="panel-grid student-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">学生端</p>
            <h3>课程筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="handleSearch">
          <label>
            学期
            <select v-model="draftFilters.termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <label>
            关键字
            <input v-model.trim="draftFilters.q" placeholder="课程、班级、教师、地点" />
          </label>

          <label>
            轮次
            <select v-model="draftRoundId" :disabled="!draftAvailableRounds.length">
              <option value="">{{ draftAvailableRounds.length ? '请选择轮次' : '无轮次' }}</option>
              <option v-for="round in draftAvailableRounds" :key="round.id" :value="String(round.id)">
                {{ round.name }}（{{ roundScopeLabel(round.target_scope) }}）
              </option>
            </select>
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">应用筛选</button>
            <button class="ghost-btn" type="button" @click="resetFilters">重置</button>
          </div>
        </form>

        <p v-if="activeRound" class="helper-text">
          当前轮次：{{ formatDateTime(activeRound.start_at) }} 至 {{ formatDateTime(activeRound.end_at) }}
        </p>
        <p v-else class="helper-text">未选择轮次时只能浏览班级，不能直接提交选课。</p>
        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">学生端</p>
            <h3>状态概览</h3>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-box">
            <span class="stat-label">班级数量</span>
            <strong>{{ total }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">我的已选</span>
            <strong>{{ myEnrollments.length }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">可用轮次数</span>
            <strong>{{ appliedAvailableRounds.length }}</strong>
          </div>
        </div>
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">课程目录</p>
          <h3>可浏览班级列表</h3>
        </div>
        <span class="badge badge-neutral">共 {{ total }} 条</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>课程</th>
              <th>班级</th>
              <th>教师</th>
              <th>上课时间</th>
              <th>地点</th>
              <th>容量</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sections" :key="item.id">
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.teacher_name }}</td>
              <td>{{ joinSectionSchedule(item) }}</td>
              <td>{{ item.location || '-' }}</td>
              <td>{{ item.capacity }}</td>
              <td>
                <div class="status-stack">
                  <span :class="['badge', resolveSectionState(item).badgeClass]">
                    {{ resolveSectionState(item).label }}
                  </span>
                  <span v-if="resolveSectionState(item).reason" class="action-note">{{ resolveSectionState(item).reason }}</span>
                </div>
              </td>
              <td class="actions">
                <RouterLink class="inline-btn link-btn" :to="`/student/courses/${item.id}`">详情</RouterLink>
                <button
                  class="inline-btn"
                  :disabled="resolveSectionState(item).disabled || enrollingId === item.id"
                  type="button"
                  @click="enroll(item)"
                >
                  {{ enrollingId === item.id ? '选课中...' : '选课' }}
                </button>
              </td>
            </tr>
            <tr v-if="!sections.length">
              <td class="table-empty" colspan="8">当前筛选条件下没有班级数据。</td>
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
import { RouterLink } from 'vue-router'

import ExpandablePanel from '../../components/ExpandablePanel.vue'
import { createEnrollment, fetchMyEnrollments, fetchRounds, fetchSections, fetchTerms, normalizeListResponse } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDateTime, joinSectionSchedule, roundScopeOptions } from '../../utils/formatters'

const terms = ref([])
const rounds = ref([])
const sections = ref([])
const myEnrollments = ref([])
const loading = ref(false)
const enrollingId = ref(null)
const draftRoundId = ref('')
const appliedRoundId = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const draftFilters = reactive({
  termId: '',
  q: '',
})

const appliedFilters = reactive({
  termId: '',
  q: '',
})

const message = reactive({
  text: '',
  type: 'success',
})

const draftAvailableRounds = computed(() =>
  draftFilters.termId ? rounds.value.filter((item) => String(item.term) === String(draftFilters.termId)) : rounds.value,
)
const appliedAvailableRounds = computed(() =>
  appliedFilters.termId ? rounds.value.filter((item) => String(item.term) === String(appliedFilters.termId)) : rounds.value,
)
const activeRound = computed(() => appliedAvailableRounds.value.find((item) => String(item.id) === appliedRoundId.value))
const enrolledSectionIds = computed(() => new Set(myEnrollments.value.map((item) => item.section_id)))
const currentRoundEnrollmentCount = computed(() => {
  if (!appliedRoundId.value) return 0
  return myEnrollments.value.filter((item) => String(item.round) === appliedRoundId.value).length
})

function roundScopeLabel(value) {
  return roundScopeOptions.find((item) => item.value === value)?.label || value
}

function isRoundOpen(round) {
  if (!round?.enabled) return false
  const now = Date.now()
  const start = new Date(round.start_at).getTime()
  const end = new Date(round.end_at).getTime()
  return Number.isFinite(start) && Number.isFinite(end) && start <= now && now <= end
}

function pickDefaultRound(roundList, termId = '') {
  const filtered = termId ? roundList.filter((item) => String(item.term) === String(termId)) : roundList
  return filtered.find(isRoundOpen) || filtered[0] || null
}

function getAvailabilityReason(section) {
  if (enrolledSectionIds.value.has(section.id)) return '你已选过该班级'
  if (!appliedRoundId.value || !activeRound.value) return '请先选择轮次并应用筛选'
  if (!isRoundOpen(activeRound.value)) return '当前轮次未开放'
  if (activeRound.value.target_scope === 'teacher') return '当前轮次不面向学生'
  if (String(section.term) !== String(activeRound.value.term)) return '当前班级不在所选轮次学期'
  if (
    Number(activeRound.value.max_courses || 0) > 0 &&
    currentRoundEnrollmentCount.value >= Number(activeRound.value.max_courses || 0)
  ) {
    return '已达到本轮选课上限'
  }
  return ''
}

function resolveSectionState(section) {
  if (enrolledSectionIds.value.has(section.id)) {
    return {
      disabled: true,
      label: '已选',
      badgeClass: 'badge-on',
      reason: '你已选过该班级',
    }
  }

  const reason = getAvailabilityReason(section)
  if (reason) {
    return {
      disabled: true,
      label: '不可选',
      badgeClass: 'badge-off',
      reason,
    }
  }

  return {
    disabled: false,
    label: '可选',
    badgeClass: 'badge-neutral',
    reason: '',
  }
}

async function loadTermsOnly() {
  terms.value = await fetchTerms()
}

async function loadPageData() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const [roundList, sectionList, enrollmentList] = await Promise.all([
        fetchRounds(),
        fetchSections({
          termId: appliedFilters.termId,
          q: appliedFilters.q,
          paginate: true,
          page: currentPage.value,
          pageSize: pageSize.value,
        }),
        fetchMyEnrollments({ termId: appliedFilters.termId }),
      ])

      rounds.value = roundList
      const { results, count } = normalizeListResponse(sectionList)
      sections.value = results
      total.value = count
      myEnrollments.value = enrollmentList

      if (!appliedAvailableRounds.value.some((item) => String(item.id) === appliedRoundId.value)) {
        const defaultRound = pickDefaultRound(rounds.value, appliedFilters.termId)
        appliedRoundId.value = defaultRound ? String(defaultRound.id) : ''
      }

      if (!draftAvailableRounds.value.some((item) => String(item.id) === draftRoundId.value)) {
        draftRoundId.value = ''
      }

      if (!draftRoundId.value && draftFilters.termId === appliedFilters.termId) {
        draftRoundId.value = appliedRoundId.value
      }
    })
  } catch (error) {
    message.text = error.message || '加载课程目录失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  appliedFilters.termId = draftFilters.termId
  appliedFilters.q = draftFilters.q
  appliedRoundId.value = draftRoundId.value
  currentPage.value = 1
  await loadPageData()
}

function resetFilters() {
  draftFilters.q = ''
  draftFilters.termId = ''
  draftRoundId.value = ''
  appliedFilters.q = ''
  appliedFilters.termId = ''
  appliedRoundId.value = ''
  currentPage.value = 1
  loadPageData()
}

function handlePageChange(page) {
  currentPage.value = page
  loadPageData()
}

async function enroll(section) {
  const state = resolveSectionState(section)
  if (state.disabled) {
    message.text = state.reason || '当前不能选择该班级。'
    message.type = 'error'
    return
  }

  enrollingId.value = section.id
  message.text = ''

  try {
    await createEnrollment({
      round_id: Number(appliedRoundId.value),
      section_id: section.id,
    })
    await loadPageData()
    message.text = `已选入 ${section.course_code} - ${section.name}。`
    message.type = 'success'
  } catch (error) {
    message.text = error.message || '该班级选课失败。'
    message.type = 'error'
  } finally {
    enrollingId.value = null
  }
}

watch(
  () => draftFilters.termId,
  () => {
    if (!draftAvailableRounds.value.some((item) => String(item.id) === draftRoundId.value)) {
      draftRoundId.value = ''
    }
  },
)

onMounted(async () => {
  try {
    await loadTermsOnly()
    await loadPageData()
  } catch (error) {
    message.text = error.message || '初始化学生课程页失败。'
    message.type = 'error'
  }
})
</script>

