from django.urls import path

from .views import CourseDetailView, CourseListCreateView, SectionDetailView, SectionListCreateView

urlpatterns = [
    path("courses", CourseListCreateView.as_view(), name="course_list_create"),
    path("courses/<int:course_id>", CourseDetailView.as_view(), name="course_detail"),
    path("sections", SectionListCreateView.as_view(), name="section_list_create"),
    path("sections/<int:section_id>", SectionDetailView.as_view(), name="section_detail"),
]
