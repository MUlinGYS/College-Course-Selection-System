<template>
  <section class="page-stack">
    <div class="panel-grid teacher-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">教师端</p>
            <h3>班级筛选</h3>
          </div>
        </div>

        <form class="filter-grid" @submit.prevent="loadSections">
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
            <p class="eyebrow">教师端</p>
            <h3>汇总信息</h3>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-box">
            <span class="stat-label">班级数</span>
            <strong>{{ sections.length }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">已选学生数</span>
            <strong>{{ totalStudents }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">总容量</span>
            <strong>{{ totalCapacity }}</strong>
          </div>
        </div>

        <div class="placeholder-state">
          <strong>本页用于查看你负责授课的班级。</strong>
          <p>点击“名单”可进入班级名单页，查看已选学生和对应选课轮次。</p>
        </div>
      </article>
    </div>

    <article class="panel-card table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">我的班级</p>
          <h3>授课班级列表</h3>
        </div>
        <span class="badge badge-neutral">{{ sections.length }} 条记录</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学期</th>
              <th>课程</th>
              <th>班级</th>
              <th>上课时间</th>
              <th>地点</th>
              <th>容量</th>
              <th>已选人数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sections" :key="item.id">
              <td>{{ item.term_name }}</td>
              <td>{{ item.course_code }} - {{ item.course_name }}</td>
              <td>{{ item.name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>{{ item.location || '-' }}</td>
              <td>{{ item.capacity }}</td>
              <td>{{ item.enrolled_count }}</td>
              <td class="actions">
                <RouterLink class="inline-btn link-btn" :to="`/teacher/sections/${item.id}/roster`">名单</RouterLink>
              </td>
            </tr>
            <tr v-if="!sections.length">
              <td class="table-empty" colspan="8">暂无授课班级。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchTeacherSections, fetchTerms } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatTime, weekdayLabel } from '../../utils/formatters'

const terms = ref([])
const sections = ref([])
const loading = ref(false)
const termId = ref('')

const message = reactive({
  text: '',
  type: 'success',
})

const totalStudents = computed(() => sections.value.reduce((sum, item) => sum + Number(item.enrolled_count || 0), 0))
const totalCapacity = computed(() => sections.value.reduce((sum, item) => sum + Number(item.capacity || 0), 0))

async function loadTermsOnly() {
  await withPageLoading(async () => {
    terms.value = await fetchTerms()
  })
}

async function loadSections() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      sections.value = await fetchTeacherSections({ termId: termId.value })
    })
  } catch (error) {
    message.text = error.message || '加载教师班级失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  termId.value = ''
  loadSections()
}

onMounted(async () => {
  try {
    await loadTermsOnly()
    await loadSections()
  } catch (error) {
    message.text = error.message || '初始化教师班级页失败。'
    message.type = 'error'
  }
})
</script>
