from django.urls import path

from .views import (
    AdminCourseApplicationListView,
    AdminCourseApplicationReviewView,
    TeacherCourseApplicationDetailView,
    TeacherCourseApplicationListCreateView,
)

urlpatterns = [
    path("teacher/course-applications", TeacherCourseApplicationListCreateView.as_view(), name="teacher_course_applications"),
    path(
        "teacher/course-applications/<int:application_id>",
        TeacherCourseApplicationDetailView.as_view(),
        name="teacher_course_application_detail",
    ),
    path("admin/course-applications", AdminCourseApplicationListView.as_view(), name="admin_course_applications"),
    path(
        "admin/course-applications/<int:application_id>/review",
        AdminCourseApplicationReviewView.as_view(),
        name="admin_course_application_review",
    ),
]

