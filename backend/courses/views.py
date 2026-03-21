from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin
from core.swagger import (
    COURSE_ID_PARAMETER,
    KEYWORD_PARAMETER,
    PAGINATION_PARAMETERS,
    TEACHER_ID_PARAMETER,
    TERM_ID_PARAMETER,
    paginated_response,
)
from .models import Course, Section
from .serializers import CourseSerializer, SectionSerializer


class AdminWriteGuardMixin:
    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None

        return Response({"message": "仅管理员可执行该操作"}, status=status.HTTP_403_FORBIDDEN)


class CourseListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    @extend_schema(
        operation_id="courses_list",
        summary="获取课程列表",
        description="查询课程库。支持关键字搜索；传入 `paginate=1` 时，返回真实分页结构。",
        parameters=PAGINATION_PARAMETERS + [KEYWORD_PARAMETER],
        responses=paginated_response("PaginatedCourseListResponse", CourseSerializer),
    )
    def get(self, request):
        queryset = Course.objects.all().order_by("id")
        keyword = request.query_params.get("q")

        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(CourseSerializer(page, many=True).data)

        return Response(CourseSerializer(queryset, many=True).data)

    @extend_schema(summary="创建课程", description="管理员创建课程库中的课程基础信息。", request=CourseSerializer, responses=CourseSerializer)
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
    serializer_class = CourseSerializer

    def get_object(self, course_id):
        return get_object_or_404(Course, pk=course_id)

    @extend_schema(operation_id="courses_detail", summary="获取课程详情", description="根据课程 ID 获取单个课程详情。", responses=CourseSerializer)
    def get(self, request, course_id):
        course = self.get_object(course_id)
        return Response(CourseSerializer(course).data)

    @extend_schema(summary="更新课程", description="管理员更新指定课程的基础信息。", request=CourseSerializer, responses=CourseSerializer)
    def put(self, request, course_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        course = self.get_object(course_id)
        serializer = CourseSerializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="删除课程", description="管理员删除指定课程。", request=None, responses={204: None})
    def delete(self, request, course_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        course = self.get_object(course_id)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SectionListCreateView(AdminWriteGuardMixin, APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SectionSerializer

    @extend_schema(
        operation_id="sections_list",
        summary="获取开课班级列表",
        description="查询开课班级。支持按学期、课程、教师和关键字筛选；传入 `paginate=1` 时，返回真实分页结构。",
        parameters=PAGINATION_PARAMETERS + [TERM_ID_PARAMETER, COURSE_ID_PARAMETER, TEACHER_ID_PARAMETER, KEYWORD_PARAMETER],
        responses=paginated_response("PaginatedSectionListResponse", SectionSerializer),
    )
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

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(SectionSerializer(page, many=True).data)

        return Response(SectionSerializer(queryset, many=True).data)

    @extend_schema(summary="创建开课班级", description="管理员为课程创建具体开课班级。", request=SectionSerializer, responses=SectionSerializer)
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
    serializer_class = SectionSerializer

    def get_object(self, section_id):
        return get_object_or_404(
            Section.objects.select_related("term", "course", "teacher", "teacher__profile"),
            pk=section_id,
        )

    @extend_schema(operation_id="sections_detail", summary="获取开课班级详情", description="根据开课班级 ID 获取详情。", responses=SectionSerializer)
    def get(self, request, section_id):
        section = self.get_object(section_id)
        return Response(SectionSerializer(section).data)

    @extend_schema(summary="更新开课班级", description="管理员更新指定开课班级信息。", request=SectionSerializer, responses=SectionSerializer)
    def put(self, request, section_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        section = self.get_object(section_id)
        serializer = SectionSerializer(section, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary="删除开课班级", description="管理员删除指定开课班级。", request=None, responses={204: None})
    def delete(self, request, section_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        section = self.get_object(section_id)
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
