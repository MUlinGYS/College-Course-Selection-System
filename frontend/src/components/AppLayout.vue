<template>
  <div class="layout-shell">
    <aside class="layout-sidebar">
      <div class="brand-block">
        <h1>校园选课系统</h1>
      </div>

      <nav class="nav-groups">
        <section v-for="group in visibleGroups" :key="group.label" class="nav-group">
          <p class="nav-group-title">{{ group.label }}</p>
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            class="nav-link"
            :class="{ active: isActive(item.to) }"
            :to="item.to"
          >
            {{ item.label }}
          </RouterLink>
        </section>
      </nav>
    </aside>

    <div class="layout-main">
      <header class="layout-topbar">
        <div class="topbar-surface">
          <div class="topbar-heading">
            <p class="eyebrow">当前页面</p>
            <h2>{{ route.meta.title || '校园选课系统' }}</h2>
            <p class="topbar-subtitle">校园选课系统</p>
          </div>

          <div class="topbar-actions">
            <div class="identity-card">
              <strong>{{ displayName }}</strong>
              <span>{{ roleLabel(currentUser.role) }} / {{ currentUser.username }}</span>
            </div>
            <button class="ghost-btn topbar-logout" type="button" @click="handleLogout">退出登录</button>
          </div>
        </div>
      </header>

      <div
        v-loading="pageLoadingState.isVisible"
        class="layout-content"
        element-loading-background="rgba(248, 251, 253, 0.72)"
        element-loading-text="页面加载中..."
        element-loading-custom-class="route-loading-mask"
      >
        <main class="page-shell" :class="{ 'page-shell-loading': pageLoadingState.isVisible }">
          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { navigationItems } from '../router/navigation'
import { authState, signOut } from '../services/auth'
import { pageLoadingState } from '../services/pageLoading'

const route = useRoute()
const router = useRouter()

const currentUser = computed(() => authState.currentUser || {})
const displayName = computed(() => currentUser.value.real_name || currentUser.value.username || '未知用户')

const visibleGroups = computed(() =>
  navigationItems
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.roles.includes(currentUser.value.role)),
    }))
    .filter((group) => group.items.length > 0),
)

function roleLabel(role) {
  return (
    {
      admin: '管理员',
      teacher: '教师',
      student: '学生',
    }[role] || role
  )
}

function isActive(path) {
  return route.path === path || route.path.startsWith(`${path}/`)
}

async function handleLogout() {
  await signOut()
  await router.replace('/login')
}
</script>
