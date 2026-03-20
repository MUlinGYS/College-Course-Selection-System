<template>
  <section class="page-stack">
    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">班级选课名单</p>
          <h3>{{ sectionTitle }}</h3>
        </div>
        <RouterLink class="ghost-btn link-btn" to="/teacher/sections">返回班级列表</RouterLink>
      </div>

      <div v-if="loading" class="placeholder-state">
        <strong>正在加载班级名单...</strong>
      </div>

      <template v-else>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">学期</span>
            <strong>{{ section.term_name || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">教师</span>
            <strong>{{ section.teacher_name || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">上课时间</span>
            <strong>{{ sectionSchedule }}</strong>
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
            <span class="detail-label">已选人数</span>
            <strong>{{ roster.length }}</strong>
          </div>
        </div>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </template>
    </article>

    <article class="panel-card table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">名单</p>
          <h3>已选学生列表</h3>
        </div>
        <span class="badge badge-neutral">{{ roster.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学生姓名</th>
              <th>用户名</th>
              <th>状态</th>
              <th>轮次</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in roster" :key="item.id">
              <td>{{ item.student_name }}</td>
              <td>{{ item.student_username }}</td>
              <td>
                <span :class="['badge', item.status === 'enrolled' ? 'badge-on' : 'badge-off']">
                  {{ enrollmentStatusLabel(item.status) }}
                </span>
              </td>
              <td>{{ item.round_name }}</td>
              <td>{{ formatDateTime(item.created_at) }}</td>
            </tr>
            <tr v-if="!roster.length">
              <td class="table-empty" colspan="5">当前还没有学生选入。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { fetchTeacherRoster, fetchTeacherSections } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { enrollmentStatusLabel, formatDateTime, formatTime, weekdayLabel } from '../../utils/formatters'

const route = useRoute()

const section = ref({})
const roster = ref([])
const loading = ref(false)
const message = reactive({
  text: '',
  type: 'success',
})

const sectionTitle = computed(() => {
  if (!section.value.course_code) return '班级详情'
  return `${section.value.course_code} - ${section.value.name}`
})

const sectionSchedule = computed(() => {
  if (!section.value.weekday) return '-'
  return `${weekdayLabel(section.value.weekday)} ${formatTime(section.value.start_time)}-${formatTime(section.value.end_time)}`
})

async function loadRoster() {
  loading.value = true
  message.text = ''

  try {
    const [sectionList, rosterList] = await withPageLoading(async () =>
      Promise.all([fetchTeacherSections(), fetchTeacherRoster(route.params.sectionId)]),
    )

    section.value = sectionList.find((item) => item.id === Number(route.params.sectionId)) || {}
    roster.value = rosterList
  } catch (error) {
    message.text = error.message || '加载名单失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRoster()
})
</script>
