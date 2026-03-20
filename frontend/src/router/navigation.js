export const navigationItems = [
  {
    label: '公共',
    items: [{ label: '个人信息', to: '/profile', roles: ['admin', 'teacher', 'student'] }],
  },
  {
    label: '管理员',
    items: [
      { label: '用户管理', to: '/admin/users', roles: ['admin'] },
      { label: '学期管理', to: '/admin/terms', roles: ['admin'] },
      { label: '轮次管理', to: '/admin/rounds', roles: ['admin'] },
      { label: '课程管理', to: '/admin/courses', roles: ['admin'] },
      { label: '开课班级', to: '/admin/sections', roles: ['admin'] },
      { label: '选课记录', to: '/admin/enrollments', roles: ['admin'] },
    ],
  },
  {
    label: '学生',
    items: [
      { label: '课程目录', to: '/student/courses', roles: ['student'] },
      { label: '我的已选', to: '/student/selected', roles: ['student'] },
      { label: '冲突检查', to: '/student/conflicts', roles: ['student'] },
      { label: '我的课表', to: '/student/timetable', roles: ['student'] },
    ],
  },
  {
    label: '教师',
    items: [{ label: '我的班级', to: '/teacher/sections', roles: ['teacher'] }],
  },
]
