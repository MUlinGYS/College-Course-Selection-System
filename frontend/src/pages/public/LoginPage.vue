<template>
  <section class="auth-shell login-shell">
    <div class="auth-card login-card">
      <div class="login-card-head">
        <div class="login-badge">选课系统</div>
        <p class="eyebrow">身份认证</p>
        <h1>校园选课系统登录</h1>
        <p class="muted">请输入账号和密码后进入系统。</p>
      </div>

      <form class="form-grid single-column" @submit.prevent="handleSubmit">
        <label>
          用户名
          <input v-model.trim="form.username" autocomplete="username" placeholder="请输入用户名" required />
        </label>

        <label>
          密码
          <input
            v-model="form.password"
            autocomplete="current-password"
            placeholder="请输入密码"
            required
            type="password"
          />
        </label>

        <div class="login-divider"></div>

        <div class="toolbar login-toolbar">
          <button class="primary-btn login-submit" :disabled="submitting" type="submit">
            {{ submitting ? '登录中...' : '登录' }}
          </button>
        </div>
      </form>

      <p v-if="message.text" :class="['message', message.type]">{{ message.text }}</p>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getDefaultRoute, loginAndLoad } from '../../services/auth'

const route = useRoute()
const router = useRouter()

const submitting = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const message = reactive({
  text: '',
  type: 'error',
})

async function handleSubmit() {
  submitting.value = true
  message.text = ''

  try {
    const user = await loginAndLoad({
      username: form.username,
      password: form.password,
    })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : getDefaultRoute(user.role)
    await router.replace(redirect)
  } catch (error) {
    message.text = error.message || '登录失败。'
    message.type = 'error'
  } finally {
    submitting.value = false
  }
}
</script>
