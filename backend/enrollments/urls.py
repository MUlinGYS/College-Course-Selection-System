from django.urls import path

from .views import (
    EnrollmentCollectionView,
    EnrollmentDetailView,
    MyConflictListView,
    MyEnrollmentListView,
    MyTimetableView,
    TeacherRosterView,
    TeacherSectionListView,
)

urlpatterns = [
    path("enrollments", EnrollmentCollectionView.as_view(), name="enrollment_collection"),
    path("enrollments/<int:enrollment_id>", EnrollmentDetailView.as_view(), name="enrollment_detail"),
    path("my/enrollments", MyEnrollmentListView.as_view(), name="my_enrollments"),
    path("my/conflicts", MyConflictListView.as_view(), name="my_conflicts"),
    path("my/timetable", MyTimetableView.as_view(), name="my_timetable"),
    path("teacher/sections", TeacherSectionListView.as_view(), name="teacher_sections"),
    path("teacher/sections/<int:section_id>/roster", TeacherRosterView.as_view(), name="teacher_roster"),
]
