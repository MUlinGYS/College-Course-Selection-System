<template>
  <div class="layout-shell">
    <aside class="layout-sidebar">
      <div class="brand-block">
        <p class="eyebrow">B/S 架构</p>
        <h1>校园选课系统</h1>
        <p class="sidebar-copy">
          当前前端已经切换为正式多页面路由结构，现有接口直接挂接到业务页面，未完成模块也保留了正式入口，便于继续迭代。
        </p>
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
        <div>
          <p class="eyebrow">当前登录</p>
          <h2>{{ route.meta.title || '校园选课系统' }}</h2>
        </div>

        <div class="topbar-actions">
          <div class="identity-card">
            <strong>{{ displayName }}</strong>
            <span>{{ roleLabel(currentUser.role) }} / {{ currentUser.username }}</span>
          </div>
          <button class="ghost-btn" type="button" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <main class="page-shell">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { navigationItems } from '../router/navigation'
import { authState, signOut } from '../services/auth'

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
