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

      <template v-if="!loading">
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
          <div class="detail-item">
            <span class="detail-label">轮次</span>
            <strong>{{ section.round_name || '-' }}</strong>
          </div>
        </div>

        <div class="action-card">
          <p v-if="activeRound" class="helper-text">
            绑定轮次：{{ activeRound.name }}（{{ roundScopeLabel(activeRound.target_scope) }}），
            {{ formatDateTime(activeRound.start_at) }} 至 {{ formatDateTime(activeRound.end_at) }}
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

import { createEnrollment, fetchMyEnrollments, fetchRound, fetchSection } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDateTime, joinSectionSchedule, roundScopeOptions } from '../../utils/formatters'

const route = useRoute()

const section = ref({})
const activeRound = ref(null)
const myEnrollments = ref([])
const loading = ref(false)
const submitting = ref(false)

const message = reactive({
  text: '',
  type: 'success',
})

const isEnrolled = computed(() => myEnrollments.value.some((item) => item.section_id === Number(route.params.sectionId)))
const currentRoundEnrollmentCount = computed(() => {
  if (!activeRound.value) return 0
  return myEnrollments.value.filter((item) => String(item.round) === String(activeRound.value.id)).length
})

const availabilityReason = computed(() => {
  if (isEnrolled.value) return '你已选过该班级'
  if (!section.value.round) return '该班级尚未绑定轮次'
  if (!activeRound.value) return '轮次信息加载失败'
  if (!isRoundOpen(activeRound.value)) return '当前轮次未开放'
  if (activeRound.value.target_scope === 'teacher') return '当前轮次不面向学生'
  if (String(section.value.round) !== String(activeRound.value.id)) return '当前班级不属于所绑定轮次'
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
    await withPageLoading(async () => {
      const detail = await fetchSection(route.params.sectionId)
      section.value = detail

      const [roundDetail, enrollmentList] = await Promise.all([
        detail.round ? fetchRound(detail.round) : Promise.resolve(null),
        fetchMyEnrollments({ termId: detail.term }),
      ])

      activeRound.value = roundDetail
      myEnrollments.value = enrollmentList
    })
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
      round_id: Number(section.value.round),
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
