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

        <form class="filter-grid" @submit.prevent="handleSearch">
          <label>
            学期
            <select v-model="termId">
              <option value="">全部学期</option>
              <option v-for="term in terms" :key="term.id" :value="String(term.id)">{{ term.name }}</option>
            </select>
          </label>

          <label>
            轮次
            <select v-model="roundId" :disabled="!availableRounds.length">
              <option value="">{{ availableRounds.length ? '全部轮次' : '无轮次' }}</option>
              <option v-for="round in availableRounds" :key="round.id" :value="String(round.id)">{{ round.name }}</option>
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
            <strong>{{ total }}</strong>
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
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">我的班级</p>
          <h3>授课班级列表</h3>
        </div>
        <span class="badge badge-neutral">共 {{ total }} 条</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学期</th>
              <th>轮次</th>
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
              <td>{{ item.round_name || '-' }}</td>
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
              <td class="table-empty" colspan="9">暂无授课班级。</td>
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
import { fetchRounds, fetchTeacherSections, fetchTerms, normalizeListResponse } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatTime, weekdayLabel } from '../../utils/formatters'

const terms = ref([])
const rounds = ref([])
const sections = ref([])
const loading = ref(false)
const termId = ref('')
const roundId = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const message = reactive({
  text: '',
  type: 'success',
})

const availableRounds = computed(() =>
  termId.value ? rounds.value.filter((item) => String(item.term) === String(termId.value)) : rounds.value,
)
const totalStudents = computed(() => sections.value.reduce((sum, item) => sum + Number(item.enrolled_count || 0), 0))
const totalCapacity = computed(() => sections.value.reduce((sum, item) => sum + Number(item.capacity || 0), 0))

async function loadBaseData() {
  await withPageLoading(async () => {
    const [termList, roundList] = await Promise.all([fetchTerms(), fetchRounds()])
    terms.value = termList
    rounds.value = roundList
  })
}

async function loadSections() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const response = await fetchTeacherSections({
        termId: termId.value,
        roundId: roundId.value,
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      sections.value = results
      total.value = count
    })
  } catch (error) {
    message.text = error.message || '加载教师班级失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  currentPage.value = 1
  await loadSections()
}

function resetFilter() {
  termId.value = ''
  roundId.value = ''
  currentPage.value = 1
  loadSections()
}

function handlePageChange(page) {
  currentPage.value = page
  loadSections()
}

watch(
  () => termId.value,
  () => {
    if (!availableRounds.value.some((item) => String(item.id) === roundId.value)) {
      roundId.value = ''
    }
  },
)

onMounted(async () => {
  try {
    await loadBaseData()
    await loadSections()
  } catch (error) {
    message.text = error.message || '初始化教师班级页失败。'
    message.type = 'error'
  }
})
</script>
