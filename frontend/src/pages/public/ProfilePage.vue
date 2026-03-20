<template>
  <section class="panel-grid profile-grid">
    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">当前用户</p>
          <h3>个人信息概览</h3>
        </div>
        <button class="ghost-btn" :disabled="loading" type="button" @click="loadProfile">刷新</button>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <span class="detail-label">用户名</span>
          <strong>{{ user.username || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">姓名</span>
          <strong>{{ user.real_name || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">角色</span>
          <strong>{{ roleLabel(user.role) }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">邮箱</span>
          <strong>{{ user.email || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">学号</span>
          <strong>{{ user.student_no || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">工号</span>
          <strong>{{ user.teacher_no || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">手机号</span>
          <strong>{{ user.phone || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">部门</span>
          <strong>{{ user.department || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">注册时间</span>
          <strong>{{ formatDateTime(user.date_joined) }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">状态</span>
          <strong>{{ user.is_enabled ? '启用' : '停用' }}</strong>
        </div>
      </div>

      <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
    </article>

    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">资料维护</p>
          <h3>编辑个人信息</h3>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="saveProfile">
        <label>
          姓名
          <input v-model.trim="profileForm.real_name" placeholder="请输入姓名" />
        </label>

        <label>
          邮箱
          <input v-model.trim="profileForm.email" placeholder="请输入邮箱" type="email" />
        </label>

        <label>
          手机号
          <input v-model.trim="profileForm.phone" placeholder="请输入手机号" />
        </label>

        <label>
          部门
          <input v-model.trim="profileForm.department" placeholder="请输入院系或部门" />
        </label>

        <div class="toolbar">
          <button class="primary-btn" :disabled="savingProfile" type="submit">
            {{ savingProfile ? '保存中...' : '保存资料' }}
          </button>
          <button class="ghost-btn" :disabled="savingProfile" type="button" @click="resetProfileForm">
            重置
          </button>
        </div>
      </form>

      <p v-if="profileMessage.text" :class="['message', profileMessage.type]">{{ profileMessage.text }}</p>
    </article>

    <article class="panel-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">账号安全</p>
          <h3>修改密码</h3>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="submitPasswordChange">
        <label>
          当前密码
          <input v-model="passwordForm.current_password" placeholder="请输入当前密码" type="password" />
        </label>

        <label>
          新密码
          <input v-model="passwordForm.new_password" placeholder="至少 6 位" type="password" />
        </label>

        <label>
          确认新密码
          <input v-model="passwordForm.confirm_password" placeholder="请再次输入新密码" type="password" />
        </label>

        <div class="toolbar">
          <button class="primary-btn" :disabled="savingPassword" type="submit">
            {{ savingPassword ? '提交中...' : '修改密码' }}
          </button>
        </div>
      </form>

      <p class="helper-text">密码修改成功后将自动退出登录，需要重新登录。</p>
      <p v-if="passwordMessage.text" :class="['message', passwordMessage.type]">{{ passwordMessage.text }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { authState, refreshCurrentUser, signOut } from '../../services/auth'
import { changeMyPassword, updateMyProfile } from '../../services/api'
import { withPageLoading } from '../../services/pageLoading'
import { formatDateTime, roleLabel } from '../../utils/formatters'

const router = useRouter()
const loading = ref(false)
const savingProfile = ref(false)
const savingPassword = ref(false)
const user = computed(() => authState.currentUser || {})
const message = reactive({
  text: '',
  type: 'success',
})
const profileMessage = reactive({
  text: '',
  type: 'success',
})
const passwordMessage = reactive({
  text: '',
  type: 'success',
})
const profileForm = reactive({
  real_name: '',
  email: '',
  phone: '',
  department: '',
})
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

function syncProfileForm() {
  profileForm.real_name = user.value.real_name || ''
  profileForm.email = user.value.email || ''
  profileForm.phone = user.value.phone || ''
  profileForm.department = user.value.department || ''
}

function resetProfileForm() {
  syncProfileForm()
  profileMessage.text = ''
}

function resetPasswordForm() {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
}

async function loadProfile() {
  loading.value = true
  message.text = ''

  try {
    await withPageLoading(async () => {
      await refreshCurrentUser()
    })
    message.text = '已从后端刷新个人信息。'
    message.type = 'success'
  } catch (error) {
    message.text = error.message || '刷新个人信息失败。'
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  savingProfile.value = true
  profileMessage.text = ''

  try {
    authState.currentUser = await updateMyProfile({ ...profileForm })
    syncProfileForm()
    profileMessage.text = '个人信息已保存。'
    profileMessage.type = 'success'
  } catch (error) {
    profileMessage.text = error.message || '保存个人信息失败。'
    profileMessage.type = 'error'
  } finally {
    savingProfile.value = false
  }
}

async function submitPasswordChange() {
  savingPassword.value = true
  passwordMessage.text = ''

  try {
    await changeMyPassword({ ...passwordForm })
    passwordMessage.text = '密码修改成功，正在返回登录页。'
    passwordMessage.type = 'success'
    resetPasswordForm()
    await signOut()
    await router.replace('/login')
  } catch (error) {
    passwordMessage.text = error.message || '修改密码失败。'
    passwordMessage.type = 'error'
  } finally {
    savingPassword.value = false
  }
}

watch(
  user,
  () => {
    syncProfileForm()
  },
  { immediate: true },
)
</script>
