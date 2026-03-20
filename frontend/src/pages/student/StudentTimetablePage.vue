<template>
  <section class="page-stack">
    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">课表</p>
          <h3>当前学期课表</h3>
        </div>

        <form class="toolbar compact-toolbar" @submit.prevent="loadTimetable">
          <select v-model="termId">
            <option value="">全部学期</option>
            <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
          </select>
          <button class="primary-btn" :disabled="loading" type="submit">{{ loading ? '加载中...' : '刷新' }}</button>
        </form>
      </div>

      <div class="stats-strip">
        <div class="stat-box">
          <span class="stat-label">课表记录数</span>
          <strong>{{ timetable.length }}</strong>
        </div>
        <div class="stat-box">
          <span class="stat-label">有课天数</span>
          <strong>{{ occupiedDays }}</strong>
        </div>
        <div class="stat-box">
          <span class="stat-label">筛选学期</span>
          <strong>{{ selectedTermName }}</strong>
        </div>
      </div>

      <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>

      <div class="timetable-grid">
        <article v-for="day in weekdays" :key="day.value" class="timetable-day">
          <h4>{{ day.label }}</h4>
          <div v-if="groupedByDay[day.value]?.length" class="timetable-list">
            <div v-for="item in groupedByDay[day.value]" :key="item.enrollment_id" class="timetable-item">
              <strong>{{ item.course_code }} - {{ item.course_name }}</strong>
              <span>{{ item.section_name }}</span>
              <span>{{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</span>
              <span>{{ item.teacher_name }}</span>
              <span>{{ item.location || '-' }}</span>
            </div>
          </div>
          <div v-else class="timetable-empty">暂无课程。</div>
        </article>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchMyTimetable, fetchTerms } from '../../services/api'
import { formatTime, weekdayOptions } from '../../utils/formatters'

const terms = ref([])
const timetable = ref([])
const loading = ref(false)
const termId = ref('')

const message = reactive({
  text: '',
  type: 'success',
})

const weekdays = weekdayOptions
const selectedTermName = computed(() => {
  if (!termId.value) return '全部学期'
  return terms.value.find((item) => String(item.id) === termId.value)?.name || '当前学期'
})
const occupiedDays = computed(() => new Set(timetable.value.map((item) => item.weekday)).size)
const groupedByDay = computed(() =>
  timetable.value.reduce((accumulator, item) => {
    if (!accumulator[item.weekday]) accumulator[item.weekday] = []
    accumulator[item.weekday].push(item)
    accumulator[item.weekday].sort((left, right) => String(left.start_time).localeCompare(String(right.start_time)))
    return accumulator
  }, {}),
)

async function loadTermsOnly() {
  terms.value = await fetchTerms()
}

async function loadTimetable() {
  loading.value = true
  message.text = ''

  try {
    timetable.value = await fetchMyTimetable({ termId: termId.value })
  } catch (error) {
    message.text = error.message || '加载课表失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadTermsOnly()
    await loadTimetable()
  } catch (error) {
    message.text = error.message || '初始化课表页面失败。'
    message.type = 'error'
  }
})
</script>
