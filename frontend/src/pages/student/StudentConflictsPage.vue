<template>
  <section class="page-stack">
    <div class="panel-grid student-grid">
      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">冲突检查</p>
            <h3>筛选条件</h3>
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

          <div class="toolbar">
            <button class="primary-btn" :disabled="loading" type="submit">执行检查</button>
            <button class="ghost-btn" type="button" @click="resetFilter">重置</button>
          </div>
        </form>

        <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">检查结果</p>
            <h3>当前状态</h3>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-box">
            <span class="stat-label">冲突对数量</span>
            <strong>{{ total }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">筛选学期</span>
            <strong>{{ selectedTermName }}</strong>
          </div>
          <div class="stat-box">
            <span class="stat-label">结果状态</span>
            <strong>{{ conflicts.length ? '发现冲突' : '无冲突' }}</strong>
          </div>
        </div>
      </article>
    </div>

    <ExpandablePanel panel-class="table-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">冲突明细</p>
          <h3>已选课程时间冲突列表</h3>
        </div>
        <span :class="['badge', total ? 'badge-off' : 'badge-on']">{{ total }} 组</span>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学期</th>
              <th>冲突时间</th>
              <th>课程 A</th>
              <th>课程 B</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in conflicts" :key="item.conflict_key">
              <td>{{ item.term_name }}</td>
              <td>{{ weekdayLabel(item.weekday) }} {{ formatTime(item.start_time) }}-{{ formatTime(item.end_time) }}</td>
              <td>
                <div class="conflict-course">
                  <strong>{{ item.first_course_code }} - {{ item.first_course_name }}</strong>
                  <span>{{ item.first_section_name }} / {{ item.first_teacher_name }}</span>
                  <span>{{ item.first_location || '-' }}</span>
                </div>
              </td>
              <td>
                <div class="conflict-course">
                  <strong>{{ item.second_course_code }} - {{ item.second_course_name }}</strong>
                  <span>{{ item.second_section_name }} / {{ item.second_teacher_name }}</span>
                  <span>{{ item.second_location || '-' }}</span>
                </div>
              </td>
              <td>{{ item.message }}</td>
            </tr>
            <tr v-if="!conflicts.length">
              <td class="table-empty" colspan="5">当前筛选条件下没有检测到课程冲突。</td>
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
import { fetchMyConflicts, fetchTerms, normalizeListResponse } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatTime, weekdayLabel } from '../../utils/formatters'

const terms = ref([])
const conflicts = ref([])
const loading = ref(false)
const termId = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const message = reactive({
  text: '',
  type: 'success',
})

const selectedTermName = computed(() => {
  if (!termId.value) return '全部学期'
  return terms.value.find((item) => String(item.id) === termId.value)?.name || '当前学期'
})

async function loadTermsOnly() {
  await withPageLoading(async () => {
    terms.value = await fetchTerms()
  })
}

async function loadConflicts() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      const response = await fetchMyConflicts({
        termId: termId.value,
        paginate: true,
        page: currentPage.value,
        pageSize: pageSize.value,
      })
      const { results, count } = normalizeListResponse(response)
      conflicts.value = results
      total.value = count
    })
    message.text = total.value ? '已完成冲突检查。' : '未检测到时间冲突。'
    message.type = 'success'
  } catch (error) {
    message.text = error.message || '加载冲突信息失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  currentPage.value = 1
  await loadConflicts()
}

function resetFilter() {
  termId.value = ''
  currentPage.value = 1
  loadConflicts()
}

function handlePageChange(page) {
  currentPage.value = page
  loadConflicts()
}

onMounted(async () => {
  try {
    await loadTermsOnly()
    await loadConflicts()
  } catch (error) {
    message.text = error.message || '初始化冲突检查页面失败。'
    message.type = 'error'
  }
})
</script>

