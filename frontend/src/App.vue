<template>
  <RouterView />
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import { authState } from './services/auth'
import { AUTH_CLEARED_EVENT } from './services/api'

const route = useRoute()
const router = useRouter()

async function handleAuthCleared() {
  authState.currentUser = null

  if (route.meta.public) {
    return
  }

  await router.replace({
    path: '/login',
    query: { redirect: route.fullPath },
  })
}

onMounted(() => {
  window.addEventListener(AUTH_CLEARED_EVENT, handleAuthCleared)
})

onBeforeUnmount(() => {
  window.removeEventListener(AUTH_CLEARED_EVENT, handleAuthCleared)
})
</script>
