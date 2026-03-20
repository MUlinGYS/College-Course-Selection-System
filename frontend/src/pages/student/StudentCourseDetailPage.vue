<template>
  <section class="page-stack">
    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">班级详情</p>
          <h3>{{ section.course_code }} - {{ section.course_name }}</h3>
        </div>
        <RouterLink class="ghost-btn link-btn" to="/student/courses">返回课程目录</RouterLink>
      </div>

      <div v-if="loading" class="placeholder-state">
        <strong>正在加载班级详情...</strong>
      </div>

      <template v-else>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">班级</span>
            <strong>{{ section.name || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">教师</span>
            <strong>{{ section.teacher_name || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">上课时间</span>
            <strong>{{ joinSectionSchedule(section) }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">地点</span>
            <strong>{{ section.location || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">容量</span>
            <strong>{{ section.capacity ?? '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">学期</span>
            <strong>{{ section.term_name || '-' }}</strong>
          </div>
        </div>

        <div class="action-card">
          <label>
            轮次
            <select v-model="selectedRoundId">
              <option value="">请选择轮次</option>
              <option v-for="round in rounds" :key="round.id" :value="String(round.id)">
                {{ round.name }}（{{ roundScopeLabel(round.target_scope) }}）
              </option>
            </select>
          </label>

          <p v-if="activeRound" class="helper-text">
            轮次时间：{{ formatDateTime(activeRound.start_at) }} 至 {{ formatDateTime(activeRound.end_at) }}
          </p>
          <p v-if="availabilityReason" class="message error">{{ availabilityReason }}</p>

          <div class="toolbar">
            <button class="primary-btn" :disabled="submitting || !!availabilityReason" type="button" @click="enroll">
              {{ buttonLabel }}
            </button>
          </div>
        </div>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </template>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { createEnrollment, fetchMyEnrollments, fetchRounds, fetchSection } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDateTime, joinSectionSchedule, roundScopeOptions } from '../../utils/formatters'

const route = useRoute()

const section = ref({})
const rounds = ref([])
const myEnrollments = ref([])
const loading = ref(false)
const submitting = ref(false)
const selectedRoundId = ref('')

const message = reactive({
  text: '',
  type: 'success',
})

const activeRound = computed(() => rounds.value.find((item) => String(item.id) === selectedRoundId.value))
const isEnrolled = computed(() => myEnrollments.value.some((item) => item.section_id === Number(route.params.sectionId)))
const currentRoundEnrollmentCount = computed(() => {
  if (!selectedRoundId.value) return 0
  return myEnrollments.value.filter((item) => String(item.round) === selectedRoundId.value).length
})

const availabilityReason = computed(() => {
  if (isEnrolled.value) return '你已选过该班级'
  if (!selectedRoundId.value || !activeRound.value) return '请先选择轮次'
  if (!isRoundOpen(activeRound.value)) return '当前轮次未开放'
  if (activeRound.value.target_scope === 'teacher') return '当前轮次不面向学生'
  if (String(section.value.term) !== String(activeRound.value.term)) return '当前班级不在所选轮次学期'
  if (
    Number(activeRound.value.max_courses || 0) > 0 &&
    currentRoundEnrollmentCount.value >= Number(activeRound.value.max_courses || 0)
  ) {
    return '已达到本轮选课上限'
  }
  return ''
})

const buttonLabel = computed(() => {
  if (submitting.value) return '提交中...'
  if (isEnrolled.value) return '已选该班级'
  if (availabilityReason.value) return '当前不可选'
  return '选这门课'
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

async function loadDetail() {
  loading.value = true
  message.text = ''

  try {
    const detail = await withPageLoading(async () => fetchSection(route.params.sectionId))
    section.value = detail

    const [roundList, enrollmentList] = await withPageLoading(async () =>
      Promise.all([fetchRounds({ termId: detail.term }), fetchMyEnrollments({ termId: detail.term })]),
    )

    rounds.value = roundList
    myEnrollments.value = enrollmentList
    const defaultRound = roundList.find(isRoundOpen) || roundList[0]
    selectedRoundId.value = defaultRound ? String(defaultRound.id) : ''
  } catch (error) {
    message.text = error.message || '加载班级详情失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function enroll() {
  if (availabilityReason.value) {
    message.text = availabilityReason.value
    message.type = 'error'
    return
  }

  submitting.value = true
  message.text = ''

  try {
    await createEnrollment({
      round_id: Number(selectedRoundId.value),
      section_id: Number(route.params.sectionId),
    })
    await loadDetail()
    message.text = '选课提交成功。'
    message.type = 'success'
  } catch (error) {
    message.text = error.message || '该班级选课失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>
