import { computed, reactive } from 'vue'

import { clearAuthTokens, fetchCurrentUser, getAccessToken, login, logout } from './api'

export const authState = reactive({
  initialized: false,
  currentUser: null,
})

export function getDefaultRoute(role) {
  if (role === 'admin') return '/admin/users'
  if (role === 'teacher') return '/teacher/sections'
  return '/student/courses'
}

export async function initializeAuth() {
  if (authState.initialized) return

  if (!getAccessToken()) {
    authState.initialized = true
    return
  }

  try {
    authState.currentUser = await fetchCurrentUser()
  } catch {
    clearAuthTokens()
    authState.currentUser = null
  } finally {
    authState.initialized = true
  }
}

export async function loginAndLoad(credentials) {
  const data = await login(credentials)
  authState.currentUser = data.user
  authState.initialized = true
  return data.user
}

export async function refreshCurrentUser() {
  try {
    authState.currentUser = await fetchCurrentUser()
    return authState.currentUser
  } catch (error) {
    authState.currentUser = null
    throw error
  }
}

export async function signOut() {
  try {
    await logout()
  } finally {
    authState.currentUser = null
    authState.initialized = true
  }
}

export function useAuth() {
  return {
    authState,
    isAuthenticated: computed(() => !!authState.currentUser),
  }
}
