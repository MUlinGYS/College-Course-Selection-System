from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin, IsTeacher
from .models import CourseApplication
from .serializers import (
    CourseApplicationReviewSerializer,
    CourseApplicationSerializer,
    CourseApplicationWriteSerializer,
    create_section_for_application,
    resolve_course_for_application,
    validate_application_teacher,
)


class ApplicationPermissionMixin:
    def ensure_teacher(self, request):
        if IsTeacher().has_permission(request, self):
            return None
        return Response({"message": "仅教师可执行该操作"}, status=status.HTTP_403_FORBIDDEN)

    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None
        return Response({"message": "仅管理员可执行该操作"}, status=status.HTTP_403_FORBIDDEN)


class TeacherCourseApplicationListCreateView(ApplicationPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = (
            CourseApplication.objects.select_related(
                "teacher",
                "teacher__profile",
                "term",
                "round",
                "reviewed_by",
                "reviewed_by__profile",
                "linked_course",
                "linked_section",
            )
            .filter(teacher=request.user)
            .order_by("id")
        )

        term_id = request.query_params.get("term_id")
        round_id = request.query_params.get("round_id")
        status_value = request.query_params.get("status")
        keyword = request.query_params.get("q")

        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if round_id:
            queryset = queryset.filter(round_id=round_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if keyword:
            queryset = queryset.filter(
                Q(course_code__icontains=keyword)
                | Q(course_name__icontains=keyword)
                | Q(section_name__icontains=keyword)
                | Q(location__icontains=keyword)
            )

        return queryset

    def get(self, request):
        denied = self.ensure_teacher(request)
        if denied:
            return denied

        queryset = self.get_queryset(request)
        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(CourseApplicationSerializer(page, many=True).data)

        return Response(CourseApplicationSerializer(queryset, many=True).data)

    def post(self, request):
        denied = self.ensure_teacher(request)
        if denied:
            return denied

        validate_application_teacher(request.user)
        serializer = CourseApplicationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(teacher=request.user)
        return Response(CourseApplicationSerializer(instance).data, status=status.HTTP_201_CREATED)


class TeacherCourseApplicationDetailView(ApplicationPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, application_id):
        return get_object_or_404(
            CourseApplication.objects.select_related(
                "teacher",
                "teacher__profile",
                "term",
                "round",
                "reviewed_by",
                "reviewed_by__profile",
                "linked_course",
                "linked_section",
            ),
            pk=application_id,
            teacher=request.user,
        )

    def put(self, request, application_id):
        denied = self.ensure_teacher(request)
        if denied:
            return denied

        instance = self.get_object(request, application_id)
        if instance.status == CourseApplication.STATUS_APPROVED:
            return Response({"message": "已通过申报不允许修改"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CourseApplicationWriteSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if instance.status == CourseApplication.STATUS_REJECTED:
            instance.status = CourseApplication.STATUS_PENDING
            instance.review_note = ""
            instance.reviewed_by = None
            instance.reviewed_at = None
            instance.linked_course = None
            instance.linked_section = None
            instance.save(
                update_fields=[
                    "status",
                    "review_note",
                    "reviewed_by",
                    "reviewed_at",
                    "linked_course",
                    "linked_section",
                    "updated_at",
                ]
            )

        return Response(CourseApplicationSerializer(instance).data)

    def delete(self, request, application_id):
        denied = self.ensure_teacher(request)
        if denied:
            return denied

        instance = self.get_object(request, application_id)
        if instance.status != CourseApplication.STATUS_PENDING:
            return Response({"message": "仅待审核申报允许删除"}, status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCourseApplicationListView(ApplicationPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        queryset = CourseApplication.objects.select_related(
            "teacher",
            "teacher__profile",
            "term",
            "round",
            "reviewed_by",
            "reviewed_by__profile",
            "linked_course",
            "linked_section",
        ).order_by("id")

        term_id = request.query_params.get("term_id")
        round_id = request.query_params.get("round_id")
        teacher_id = request.query_params.get("teacher_id")
        status_value = request.query_params.get("status")
        keyword = request.query_params.get("q")

        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if round_id:
            queryset = queryset.filter(round_id=round_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if keyword:
            queryset = queryset.filter(
                Q(course_code__icontains=keyword)
                | Q(course_name__icontains=keyword)
                | Q(section_name__icontains=keyword)
                | Q(location__icontains=keyword)
                | Q(teacher__username__icontains=keyword)
                | Q(teacher__profile__real_name__icontains=keyword)
            )

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(CourseApplicationSerializer(page, many=True).data)

        return Response(CourseApplicationSerializer(queryset, many=True).data)


class AdminCourseApplicationReviewView(ApplicationPermissionMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        application = get_object_or_404(
            CourseApplication.objects.select_related("teacher", "teacher__profile", "term", "round"),
            pk=application_id,
        )
        if application.status != CourseApplication.STATUS_PENDING:
            return Response({"message": "该申报已审核，不能重复处理"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CourseApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        review_note = serializer.validated_data["review_note"]

        with transaction.atomic():
            application.review_note = review_note
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()

            if action == "reject":
                application.status = CourseApplication.STATUS_REJECTED
                application.save(
                    update_fields=[
                        "status",
                        "review_note",
                        "reviewed_by",
                        "reviewed_at",
                        "updated_at",
                    ]
                )
                return Response(CourseApplicationSerializer(application).data)

            validate_application_teacher(application.teacher)
            course = resolve_course_for_application(application)
            section = create_section_for_application(application, course)

            application.status = CourseApplication.STATUS_APPROVED
            application.linked_course = course
            application.linked_section = section
            application.save(
                update_fields=[
                    "status",
                    "review_note",
                    "reviewed_by",
                    "reviewed_at",
                    "linked_course",
                    "linked_section",
                    "updated_at",
                ]
            )

        return Response(CourseApplicationSerializer(application).data)
