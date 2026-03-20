import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '../components/AppLayout.vue'
import AdminCoursesPage from '../pages/admin/AdminCoursesPage.vue'
import AdminEnrollmentsPage from '../pages/admin/AdminEnrollmentsPage.vue'
import AdminRoundsPage from '../pages/admin/AdminRoundsPage.vue'
import AdminSectionsPage from '../pages/admin/AdminSectionsPage.vue'
import AdminTermsPage from '../pages/admin/AdminTermsPage.vue'
import AdminUsersPage from '../pages/admin/AdminUsersPage.vue'
import LoginPage from '../pages/public/LoginPage.vue'
import NotFoundPage from '../pages/public/NotFoundPage.vue'
import ProfilePage from '../pages/public/ProfilePage.vue'
import StudentConflictsPage from '../pages/student/StudentConflictsPage.vue'
import StudentCourseDetailPage from '../pages/student/StudentCourseDetailPage.vue'
import StudentCoursesPage from '../pages/student/StudentCoursesPage.vue'
import StudentSelectedPage from '../pages/student/StudentSelectedPage.vue'
import StudentTimetablePage from '../pages/student/StudentTimetablePage.vue'
import TeacherRosterPage from '../pages/teacher/TeacherRosterPage.vue'
import TeacherSectionsPage from '../pages/teacher/TeacherSectionsPage.vue'
import { authState, getDefaultRoute, initializeAuth } from '../services/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      { path: '', redirect: '/profile' },
      { path: 'profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true, title: '个人信息' } },
      { path: 'admin/users', name: 'admin-users', component: AdminUsersPage, meta: { requiresAuth: true, roles: ['admin'], title: '用户管理' } },
      { path: 'admin/terms', name: 'admin-terms', component: AdminTermsPage, meta: { requiresAuth: true, roles: ['admin'], title: '学期管理' } },
      { path: 'admin/rounds', name: 'admin-rounds', component: AdminRoundsPage, meta: { requiresAuth: true, roles: ['admin'], title: '轮次管理' } },
      { path: 'admin/courses', name: 'admin-courses', component: AdminCoursesPage, meta: { requiresAuth: true, roles: ['admin'], title: '课程管理' } },
      { path: 'admin/sections', name: 'admin-sections', component: AdminSectionsPage, meta: { requiresAuth: true, roles: ['admin'], title: '开课班级' } },
      { path: 'admin/enrollments', name: 'admin-enrollments', component: AdminEnrollmentsPage, meta: { requiresAuth: true, roles: ['admin'], title: '选课记录' } },
      { path: 'student/courses', name: 'student-courses', component: StudentCoursesPage, meta: { requiresAuth: true, roles: ['student'], title: '课程目录' } },
      { path: 'student/courses/:sectionId', name: 'student-course-detail', component: StudentCourseDetailPage, meta: { requiresAuth: true, roles: ['student'], title: '课程详情' } },
      { path: 'student/selected', name: 'student-selected', component: StudentSelectedPage, meta: { requiresAuth: true, roles: ['student'], title: '我的已选' } },
      { path: 'student/conflicts', name: 'student-conflicts', component: StudentConflictsPage, meta: { requiresAuth: true, roles: ['student'], title: '冲突检查' } },
      { path: 'student/timetable', name: 'student-timetable', component: StudentTimetablePage, meta: { requiresAuth: true, roles: ['student'], title: '我的课表' } },
      { path: 'teacher/sections', name: 'teacher-sections', component: TeacherSectionsPage, meta: { requiresAuth: true, roles: ['teacher'], title: '我的班级' } },
      { path: 'teacher/sections/:sectionId/roster', name: 'teacher-roster', component: TeacherRosterPage, meta: { requiresAuth: true, roles: ['teacher'], title: '选课名单' } },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundPage,
    meta: { public: true, title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  await initializeAuth()

  if (to.meta.public) {
    if (to.name === 'login' && authState.currentUser) {
      return getDefaultRoute(authState.currentUser.role)
    }
    return true
  }

  if (!authState.currentUser) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(authState.currentUser.role)) {
    return getDefaultRoute(authState.currentUser.role)
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} | 校园选课系统` : '校园选课系统'
})

export default router
