export const roleOptions = [
  { value: 'student', label: '学生' },
  { value: 'teacher', label: '教师' },
  { value: 'admin', label: '管理员' },
]

export const weekdayOptions = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

export const roundScopeOptions = [
  { value: 'all', label: '全部用户' },
  { value: 'student', label: '仅学生' },
  { value: 'teacher', label: '仅教师' },
]

export const enrollmentStatusOptions = [
  { value: 'enrolled', label: '已选' },
  { value: 'dropped', label: '已退' },
]

export const courseApplicationStatusOptions = [
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
]

export function roleLabel(role) {
  return roleOptions.find((item) => item.value === role)?.label || role || '-'
}

export function weekdayLabel(weekday) {
  return weekdayOptions.find((item) => item.value === Number(weekday))?.label || '-'
}

export function enrollmentStatusLabel(status) {
  return enrollmentStatusOptions.find((item) => item.value === status)?.label || status || '-'
}

export function courseApplicationStatusLabel(status) {
  return courseApplicationStatusOptions.find((item) => item.value === status)?.label || status || '-'
}

export function formatDate(value) {
  if (!value) return '-'
  return String(value).slice(0, 10)
}

export function formatTime(value) {
  if (!value) return '-'
  return String(value).slice(0, 5)
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hour = `${date.getHours()}`.padStart(2, '0')
  const minute = `${date.getMinutes()}`.padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

export function toDateTimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hour = `${date.getHours()}`.padStart(2, '0')
  const minute = `${date.getMinutes()}`.padStart(2, '0')
  return `${year}-${month}-${day}T${hour}:${minute}`
}

export function toIsoDateTime(value) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

export function joinSectionSchedule(section) {
  return `${weekdayLabel(section.weekday)} ${formatTime(section.start_time)}-${formatTime(section.end_time)}`
}

export function buildSelectOptions(list, valueKey = 'id', labelBuilder = (item) => item.name) {
  return list.map((item) => ({
    value: item[valueKey],
    label: labelBuilder(item),
  }))
}
