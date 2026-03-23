from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin, IsTeacher
from core.swagger import (
    KEYWORD_PARAMETER,
    PAGINATION_PARAMETERS,
    ROUND_ID_PARAMETER,
    STATUS_PARAMETER,
    TEACHER_ID_PARAMETER,
    TERM_ID_PARAMETER,
    paginated_response,
)
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
    serializer_class = CourseApplicationSerializer

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

    @extend_schema(
        summary="获取我的开课申报列表",
        description="教师查询自己提交的开课申报。",
        parameters=PAGINATION_PARAMETERS + [TERM_ID_PARAMETER, ROUND_ID_PARAMETER, STATUS_PARAMETER, KEYWORD_PARAMETER],
        responses=paginated_response("PaginatedTeacherCourseApplicationListResponse", CourseApplicationSerializer),
    )
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

    @extend_schema(
        summary="提交开课申报",
        description="教师提交新的开课申报，申报必须绑定学期和轮次。",
        request=CourseApplicationWriteSerializer,
        responses=CourseApplicationSerializer,
    )
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
    serializer_class = CourseApplicationSerializer

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

    @extend_schema(
        summary="修改开课申报",
        description="教师修改自己的开课申报。已通过的申报不可修改。",
        request=CourseApplicationWriteSerializer,
        responses=CourseApplicationSerializer,
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

    @extend_schema(summary="删除开课申报", description="教师删除自己的待审核开课申报。", request=None, responses={204: None})
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
    serializer_class = CourseApplicationSerializer

    @extend_schema(
        summary="获取开课申报审核列表",
        description="管理员查询所有教师开课申报。",
        parameters=PAGINATION_PARAMETERS + [TERM_ID_PARAMETER, ROUND_ID_PARAMETER, TEACHER_ID_PARAMETER, STATUS_PARAMETER, KEYWORD_PARAMETER],
        responses=paginated_response("PaginatedAdminCourseApplicationListResponse", CourseApplicationSerializer),
    )
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
    serializer_class = CourseApplicationSerializer

    @extend_schema(
        summary="审核开课申报",
        description="管理员对待审核开课申报执行通过或驳回。通过后会自动落地为课程和开课班级。",
        request=CourseApplicationReviewSerializer,
        responses=CourseApplicationSerializer,
    )
    def post(self, request, application_id):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        serializer = CourseApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        review_note = serializer.validated_data["review_note"]

        with transaction.atomic():
            application = get_object_or_404(
                CourseApplication.objects.select_related("teacher", "teacher__profile", "term", "round").select_for_update(),
                pk=application_id,
            )
            if application.status != CourseApplication.STATUS_PENDING:
                return Response({"message": "该申报已审核，不能重复处理"}, status=status.HTTP_400_BAD_REQUEST)

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
            try:
                section = create_section_for_application(application, course)
            except IntegrityError:
                return Response(
                    {"message": "该申报已被处理，或已生成同名班级，请刷新后重试"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
