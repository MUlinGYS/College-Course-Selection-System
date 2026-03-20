from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin
from .models import Course, Section
from .serializers import CourseSerializer, SectionSerializer


class AdminWriteGuardMixin:
    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None

        return Response({"message": "仅管理员可执行该操作"}, status=status.HTTP_403_FORBIDDEN)


class CourseListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Course.objects.all().order_by("id")
        keyword = request.query_params.get("q")

        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))

        return Response(CourseSerializer(queryset, many=True).data)

    def post(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseDetailView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, course_id):
        return get_object_or_404(Course, pk=course_id)

    def get(self, request, course_id):
        course = self.get_object(course_id)
        return Response(CourseSerializer(course).data)

    def put(self, request, course_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        course = self.get_object(course_id)
        serializer = CourseSerializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, course_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        course = self.get_object(course_id)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SectionListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Section.objects.select_related("term", "course", "teacher", "teacher__profile").all().order_by("id")
        term_id = request.query_params.get("term_id")
        course_id = request.query_params.get("course_id")
        teacher_id = request.query_params.get("teacher_id")
        keyword = request.query_params.get("q")

        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(location__icontains=keyword)
                | Q(course__name__icontains=keyword)
                | Q(course__code__icontains=keyword)
                | Q(teacher__username__icontains=keyword)
                | Q(teacher__profile__real_name__icontains=keyword)
            )

        return Response(SectionSerializer(queryset, many=True).data)

    def post(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        serializer = SectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SectionDetailView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, section_id):
        return get_object_or_404(
            Section.objects.select_related("term", "course", "teacher", "teacher__profile"),
            pk=section_id,
        )

    def get(self, request, section_id):
        section = self.get_object(section_id)
        return Response(SectionSerializer(section).data)

    def put(self, request, section_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        section = self.get_object(section_id)
        serializer = SectionSerializer(section, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, section_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        section = self.get_object(section_id)
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
