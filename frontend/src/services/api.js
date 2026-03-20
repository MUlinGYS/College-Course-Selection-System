const API_BASE = '/api'
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
export const AUTH_CLEARED_EVENT = 'auth:cleared'

function parseResponse(text) {
  if (!text) return null

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function normalizeErrorMessage(data, status) {
  if (typeof data === 'string') return data
  if (data?.message) return data.message
  if (data?.detail) return data.detail

  if (data && typeof data === 'object') {
    const entries = Object.entries(data)
      .map(([field, value]) => {
        const message = Array.isArray(value) ? value.join(' ') : String(value)
        return `${field}: ${message}`
      })
      .filter(Boolean)

    if (entries.length) return entries.join(' | ')
  }

  return `请求失败：${status}`
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function saveAuthTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
  if (refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
}

export function clearAuthTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  window.dispatchEvent(new CustomEvent(AUTH_CLEARED_EVENT))
}

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  return fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

function shouldRefreshToken(response, data, path) {
  if (response.status !== 401) return false
  if (path === '/auth/login/' || path === '/auth/refresh/' || path === '/auth/logout/') return false
  if (!getRefreshToken()) return false

  return true
}

async function apiFetch(path, { method = 'GET', body, retry = true } = {}) {
  let response = await request(path, { method, body, token: getAccessToken() })
  let data = parseResponse(await response.text())

  if (shouldRefreshToken(response, data, path) && retry && getRefreshToken()) {
    try {
      await refreshAccessToken()
      response = await request(path, { method, body, token: getAccessToken() })
      data = parseResponse(await response.text())
    } catch {
      clearAuthTokens()
      throw new Error('登录已过期，请重新登录')
    }
  }

  if (!response.ok) {
    if (response.status === 401) clearAuthTokens()
    throw new Error(normalizeErrorMessage(data, response.status))
  }

  return data
}

export function apiGet(path) {
  return apiFetch(path, { method: 'GET' })
}

export function apiPost(path, body) {
  return apiFetch(path, { method: 'POST', body })
}

export function apiPut(path, body) {
  return apiFetch(path, { method: 'PUT', body })
}

export function apiDelete(path) {
  return apiFetch(path, { method: 'DELETE' })
}

function applyPaginationParams(params, { paginate = false, page = '', pageSize = '' } = {}) {
  if (paginate) params.set('paginate', '1')
  if (page) params.set('page', String(page))
  if (pageSize) params.set('page_size', String(pageSize))
}

export function normalizeListResponse(data) {
  if (Array.isArray(data)) {
    return {
      results: data,
      count: data.length,
    }
  }

  return {
    results: Array.isArray(data?.results) ? data.results : [],
    count: Number(data?.count || 0),
  }
}

export function fetchHealth() {
  return apiGet('/health/')
}

export async function login(credentials) {
  const data = await apiPost('/auth/login/', credentials)
  saveAuthTokens(data)
  return data
}

export async function refreshAccessToken() {
  const refresh_token = getRefreshToken()
  if (!refresh_token) throw new Error('缺少刷新令牌')

  const data = await apiFetch('/auth/refresh/', {
    method: 'POST',
    body: { refresh: refresh_token, refresh_token },
    retry: false,
  })
  saveAuthTokens(data)
  return data
}

export async function logout() {
  try {
    await apiPost('/auth/logout/', { refresh_token: getRefreshToken() })
  } finally {
    clearAuthTokens()
  }
}

export function fetchCurrentUser() {
  return apiGet('/me')
}

export function updateMyProfile(payload) {
  return apiPut('/me', payload)
}

export function changeMyPassword(payload) {
  return apiPost('/me/password', payload)
}

export function fetchUsers({ role = '', q = '', page = '', pageSize = '', paginate = false } = {}) {
  const params = new URLSearchParams()
  if (role) params.set('role', role)
  if (q) params.set('q', q)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/users${query ? `?${query}` : ''}`)
}

export function createUser(payload) {
  return apiPost('/users', payload)
}

export function updateUser(userId, payload) {
  return apiPut(`/users/${userId}`, payload)
}

export function deleteUser(userId) {
  return apiDelete(`/users/${userId}`)
}

export function fetchTerms({ paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/terms${query ? `?${query}` : ''}`)
}

export function fetchTerm(termId) {
  return apiGet(`/terms/${termId}`)
}

export function createTerm(payload) {
  return apiPost('/terms', payload)
}

export function updateTerm(termId, payload) {
  return apiPut(`/terms/${termId}`, payload)
}

export function fetchRounds({ termId = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (termId) params.set('term_id', termId)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/rounds${query ? `?${query}` : ''}`)
}

export function fetchRound(roundId) {
  return apiGet(`/rounds/${roundId}`)
}

export function createRound(payload) {
  return apiPost('/rounds', payload)
}

export function updateRound(roundId, payload) {
  return apiPut(`/rounds/${roundId}`, payload)
}

export function fetchCourses({ q = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/courses${query ? `?${query}` : ''}`)
}

export function fetchCourse(courseId) {
  return apiGet(`/courses/${courseId}`)
}

export function createCourse(payload) {
  return apiPost('/courses', payload)
}

export function updateCourse(courseId, payload) {
  return apiPut(`/courses/${courseId}`, payload)
}

export function deleteCourse(courseId) {
  return apiDelete(`/courses/${courseId}`)
}

export function fetchSections({ termId = '', courseId = '', teacherId = '', q = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (termId) params.set('term_id', termId)
  if (courseId) params.set('course_id', courseId)
  if (teacherId) params.set('teacher_id', teacherId)
  if (q) params.set('q', q)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/sections${query ? `?${query}` : ''}`)
}

export function fetchSection(sectionId) {
  return apiGet(`/sections/${sectionId}`)
}

export function createSection(payload) {
  return apiPost('/sections', payload)
}

export function updateSection(sectionId, payload) {
  return apiPut(`/sections/${sectionId}`, payload)
}

export function deleteSection(sectionId) {
  return apiDelete(`/sections/${sectionId}`)
}

export function createEnrollment(payload) {
  return apiPost('/enrollments', payload)
}

export function deleteEnrollment(enrollmentId) {
  return apiDelete(`/enrollments/${enrollmentId}`)
}

export function fetchMyEnrollments({ termId = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (termId) params.set('term_id', termId)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/my/enrollments${query ? `?${query}` : ''}`)
}

export function fetchMyTimetable({ termId = '' } = {}) {
  const query = termId ? `?term_id=${termId}` : ''
  return apiGet(`/my/timetable${query}`)
}

export function fetchMyConflicts({ termId = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (termId) params.set('term_id', termId)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/my/conflicts${query ? `?${query}` : ''}`)
}

export function fetchTeacherSections({ termId = '', paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  if (termId) params.set('term_id', termId)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/teacher/sections${query ? `?${query}` : ''}`)
}

export function fetchTeacherRoster(sectionId, { paginate = false, page = '', pageSize = '' } = {}) {
  const params = new URLSearchParams()
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/teacher/sections/${sectionId}/roster${query ? `?${query}` : ''}`)
}

export function fetchEnrollmentRecords({
  roundId = '',
  sectionId = '',
  studentId = '',
  status = '',
  paginate = false,
  page = '',
  pageSize = '',
} = {}) {
  const params = new URLSearchParams()
  if (roundId) params.set('round_id', roundId)
  if (sectionId) params.set('section_id', sectionId)
  if (studentId) params.set('student_id', studentId)
  if (status) params.set('status', status)
  applyPaginationParams(params, { paginate, page, pageSize })
  const query = params.toString()
  return apiGet(`/enrollments${query ? `?${query}` : ''}`)
}
