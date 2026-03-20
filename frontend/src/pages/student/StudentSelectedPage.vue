<template>
  <section class="page-stack">
    <div class="panel-grid student-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">我的已选</p>
            <h3>筛选条件</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadEnrollments">
          <label>
            学期
            <select v-model="termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">应用筛选</button>
            <button class="ghost-btn" type="button" @click="resetFilter">重置</button>
          </div>
        </form>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">当前说明</p>
            <h3>退课规则</h3>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-box">
            <span class="stat-label">已选课程数</span>
            <strong>{{ enrollments.length }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">筛选学期</span>
            <strong>{{ selectedTermName }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">当前状态</span>
            <strong>已选</strong>
          </div>
        </div>

        <div class="placeholder-state">
          <strong>是否允许退课由后端轮次配置决定。</strong>
          <p>如果当前轮次不允许退课或已关闭，后端会拒绝请求并返回中文原因。本页只展示当前仍处于已选状态的课程。</p>
        </div>
      </article>
    </div>

    <article class="panel-card table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">我的已选</p>
          <h3>当前已选课程</h3>
        </div>
        <span class="badge badge-neutral">{{ enrollments.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学期</th>
              <th>轮次</th>
              <th>课程</th>
              <th>班级</th>
              <th>教师</th>
              <th>上课时间</th>
              <th>地点</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in enrollments" :key="item.id">
              <td>{{ item.term_name }}</td>
              <td>{{ item.round_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.section_name }}</td>
              <td>{{ item.teacher_name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>{{ item.location || '-' }}</td>
              <td class="actions">
                <button
                  class="inline-btn danger"
                  :disabled="droppingId === item.id"
                  type="button"
                  @click="dropEnrollment(item)"
                >
                  {{ droppingId === item.id ? '退课中...' : '退课' }}
                </button>
              </td>
            </tr>
            <tr v-if="!enrollments.length">
              <td class="table-empty" colspan="8">当前没有已选课程。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { deleteEnrollment, fetchMyEnrollments, fetchTerms } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatTime, weekdayLabel } from '../../utils/formatters'

const terms = ref([])
const enrollments = ref([])
const loading = ref(false)
const droppingId = ref(null)
const termId = ref('')

const message = reactive({
  text: '',
  type: 'success',
})

const selectedTermName = computed(() => {
  if (!termId.value) return '全部学期'
  return terms.value.find((item) => String(item.id) === termId.value)?.name || '当前学期'
})

async function loadTermsOnly() {
  terms.value = await fetchTerms()
}

async function loadEnrollments() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      enrollments.value = await fetchMyEnrollments({ termId: termId.value })
    })
  } catch (error) {
    message.text = error.message || '加载我的已选失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  termId.value = ''
  loadEnrollments()
}

async function dropEnrollment(item) {
  const accepted = window.confirm(`确认退选 ${item.course_code} - ${item.section_name} 吗？`)
  if (!accepted) return

  droppingId.value = item.id

  try {
    await deleteEnrollment(item.id)
    await loadEnrollments()
    message.text = '退课成功。'
    message.type = 'success'
  } catch (error) {
    message.text = error.message || '退课失败。'
    message.type = 'error'
  } finally {
    droppingId.value = null
  }
}

onMounted(async () => {
  try {
    await loadTermsOnly()
    await loadEnrollments()
  } catch (error) {
    message.text = error.message || '初始化我的已选页面失败。'
    message.type = 'error'
  }
})
</script>
