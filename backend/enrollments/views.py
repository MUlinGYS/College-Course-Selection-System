from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin
from core.redis_lock import RedisLockBusy, RedisLockUnavailable, guarded_redis_locks
from core.utils import ensure_user_profile
from courses.models import Section
from rounds.models import Round
from users.models import UserProfile
from .models import Enrollment
from .serializers import ConflictSerializer, EnrollmentSerializer, EnrollmentWriteSerializer, TimetableSerializer


def error_response(code, message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({"code": code, "message": message}, status=http_status)


def is_time_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


class StudentGuardMixin:
    def ensure_student(self, request):
        profile = ensure_user_profile(request.user)
        if request.user.is_superuser or profile.role == UserProfile.ROLE_STUDENT:
            return None

        return error_response("FORBIDDEN", "仅学生可执行该操作", status.HTTP_403_FORBIDDEN)


class TeacherOrAdminGuardMixin:
    def ensure_teacher_or_admin(self, request):
        if request.user.is_superuser:
            return None

        profile = ensure_user_profile(request.user)
        if profile.role in {UserProfile.ROLE_TEACHER, UserProfile.ROLE_ADMIN}:
            return None

        return error_response("FORBIDDEN", "仅教师或管理员可执行该操作", status.HTTP_403_FORBIDDEN)


class AdminGuardMixin:
    def ensure_admin(self, request):
        if IsAdmin().has_permission(request, self):
            return None

        return error_response("FORBIDDEN", "仅管理员可执行该操作", status.HTTP_403_FORBIDDEN)


class EnrollmentCollectionView(StudentGuardMixin, AdminGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_admin(request)
        if denied:
            return denied

        queryset = Enrollment.objects.select_related(
            "student",
            "student__profile",
            "round",
            "section",
            "section__term",
            "section__course",
            "section__teacher",
            "section__teacher__profile",
        ).all()

        round_id = request.query_params.get("round_id")
        section_id = request.query_params.get("section_id")
        student_id = request.query_params.get("student_id")
        status_value = request.query_params.get("status")

        if round_id:
            queryset = queryset.filter(round_id=round_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status_value:
            queryset = queryset.filter(status=status_value)

        queryset = queryset.order_by("id")
        return Response(EnrollmentSerializer(queryset, many=True).data)

    def post(self, request):
        denied = self.ensure_student(request)
        if denied:
            return denied

        serializer = EnrollmentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = request.user
        round_id = serializer.validated_data["round_id"]
        section_id = serializer.validated_data["section_id"]

        lock_names = [
            f"enrollment:student:{student.id}:round:{round_id}",
            f"enrollment:section:{section_id}",
        ]

        try:
            with guarded_redis_locks(lock_names):
                with transaction.atomic():
                    round_instance = get_object_or_404(Round.objects.select_related("term"), pk=round_id)
                    section = get_object_or_404(
                        Section.objects.select_related("term", "course", "teacher", "teacher__profile").select_for_update(),
                        pk=section_id,
                    )

                    now = timezone.now()
                    if not round_instance.enabled or now < round_instance.start_at or now > round_instance.end_at:
                        return error_response("ROUND_CLOSED", "当前轮次未开放，暂时不能选课")

                    if section.term_id != round_instance.term_id:
                        return error_response("ROUND_SECTION_MISMATCH", "所选班级不属于当前轮次对应学期")

                    profile = ensure_user_profile(student)
                    if round_instance.target_scope == Round.SCOPE_STUDENT and profile.role != UserProfile.ROLE_STUDENT:
                        return error_response("FORBIDDEN_SCOPE", "当前轮次仅允许学生参与")

                    existing = Enrollment.objects.filter(
                        student=student,
                        round=round_instance,
                        section=section,
                    ).first()
                    if existing and existing.status == Enrollment.STATUS_ENROLLED:
                        return error_response("DUPLICATE", "你已经选过这个班级了")

                    if round_instance.max_courses > 0:
                        active_count = Enrollment.objects.filter(
                            student=student,
                            round=round_instance,
                            status=Enrollment.STATUS_ENROLLED,
                        ).count()
                        if not existing or existing.status != Enrollment.STATUS_ENROLLED:
                            if active_count >= round_instance.max_courses:
                                return error_response("LIMIT_EXCEEDED", "已超过当前轮次的选课上限")

                    active_same_section = Enrollment.objects.filter(
                        section=section,
                        status=Enrollment.STATUS_ENROLLED,
                    ).count()
                    if (not existing or existing.status != Enrollment.STATUS_ENROLLED) and active_same_section >= section.capacity:
                        return error_response("FULL", "该班级人数已满")

                    active_term_enrollments = Enrollment.objects.select_related(
                        "section",
                        "section__course",
                        "section__teacher",
                        "section__term",
                    ).filter(
                        student=student,
                        status=Enrollment.STATUS_ENROLLED,
                        section__term=section.term,
                    )

                    for enrolled in active_term_enrollments:
                        if enrolled.section_id == section.id:
                            continue
                        if enrolled.section.weekday != section.weekday:
                            continue
                        if is_time_overlap(
                            enrolled.section.start_time,
                            enrolled.section.end_time,
                            section.start_time,
                            section.end_time,
                        ):
                            return error_response("TIME_CONFLICT", "该班级与已选课程时间冲突")

                    if existing and existing.status == Enrollment.STATUS_DROPPED:
                        existing.status = Enrollment.STATUS_ENROLLED
                        existing.round = round_instance
                        existing.save(update_fields=["status", "round", "updated_at"])
                        enrollment = existing
                    else:
                        enrollment = Enrollment.objects.create(
                            student=student,
                            round=round_instance,
                            section=section,
                            status=Enrollment.STATUS_ENROLLED,
                        )

                    return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)
        except RedisLockBusy:
            return error_response("REQUEST_BUSY", "当前选课请求较多，请稍后重试", status.HTTP_409_CONFLICT)
        except RedisLockUnavailable:
            return error_response("REDIS_UNAVAILABLE", "选课锁服务暂不可用，请稍后重试", status.HTTP_503_SERVICE_UNAVAILABLE)


class EnrollmentDetailView(StudentGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, enrollment_id):
        denied = self.ensure_student(request)
        if denied:
            return denied

        enrollment = get_object_or_404(
            Enrollment.objects.select_related("round", "section"),
            pk=enrollment_id,
            student=request.user,
        )

        if enrollment.status != Enrollment.STATUS_ENROLLED:
            return error_response("NOT_ENROLLED", "该选课记录当前不是已选状态")

        if not enrollment.round.allow_drop:
            return error_response("DROP_NOT_ALLOWED", "当前轮次不允许退课")

        now = timezone.now()
        if not enrollment.round.enabled or now < enrollment.round.start_at or now > enrollment.round.end_at:
            return error_response("ROUND_CLOSED", "当前轮次未开放，暂时不能退课")

        enrollment.status = Enrollment.STATUS_DROPPED
        enrollment.save(update_fields=["status", "updated_at"])
        return Response({"ok": True})


class MyEnrollmentListView(StudentGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_student(request)
        if denied:
            return denied

        queryset = Enrollment.objects.select_related(
            "round",
            "section",
            "section__term",
            "section__course",
            "section__teacher",
            "section__teacher__profile",
            "student",
            "student__profile",
        ).filter(
            student=request.user,
            status=Enrollment.STATUS_ENROLLED,
        )

        term_id = request.query_params.get("term_id")
        if term_id:
            queryset = queryset.filter(section__term_id=term_id)

        queryset = queryset.order_by("id")
        return Response(EnrollmentSerializer(queryset, many=True).data)


class MyTimetableView(StudentGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_student(request)
        if denied:
            return denied

        queryset = Enrollment.objects.select_related(
            "section",
            "section__course",
            "section__teacher",
            "section__teacher__profile",
            "section__term",
        ).filter(
            student=request.user,
            status=Enrollment.STATUS_ENROLLED,
        ).order_by("section__weekday", "section__start_time", "id")

        term_id = request.query_params.get("term_id")
        if term_id:
            queryset = queryset.filter(section__term_id=term_id)

        timetable = [
            {
                "enrollment_id": item.id,
                "course_id": item.section.course_id,
                "course_code": item.section.course.code,
                "course_name": item.section.course.name,
                "section_id": item.section_id,
                "section_name": item.section.name,
                "teacher_name": item.section.teacher.profile.real_name if getattr(item.section.teacher, "profile", None) and item.section.teacher.profile.real_name else item.section.teacher.username,
                "weekday": item.section.weekday,
                "start_time": item.section.start_time,
                "end_time": item.section.end_time,
                "location": item.section.location,
            }
            for item in queryset
        ]

        return Response(TimetableSerializer(timetable, many=True).data)


class MyConflictListView(StudentGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_student(request)
        if denied:
            return denied

        queryset = list(
            Enrollment.objects.select_related(
                "section",
                "section__course",
                "section__teacher",
                "section__teacher__profile",
                "section__term",
            ).filter(
                student=request.user,
                status=Enrollment.STATUS_ENROLLED,
            ).order_by("section__term_id", "section__weekday", "section__start_time", "id")
        )

        term_id = request.query_params.get("term_id")
        if term_id:
            queryset = [item for item in queryset if str(item.section.term_id) == str(term_id)]

        conflicts = []
        for index, first in enumerate(queryset):
            for second in queryset[index + 1 :]:
                if first.section.term_id != second.section.term_id:
                    continue
                if first.section.weekday != second.section.weekday:
                    continue
                if not is_time_overlap(
                    first.section.start_time,
                    first.section.end_time,
                    second.section.start_time,
                    second.section.end_time,
                ):
                    continue

                overlap_start = max(first.section.start_time, second.section.start_time)
                overlap_end = min(first.section.end_time, second.section.end_time)
                first_teacher_profile = getattr(first.section.teacher, "profile", None)
                second_teacher_profile = getattr(second.section.teacher, "profile", None)

                conflicts.append(
                    {
                        "conflict_key": f"{first.id}-{second.id}",
                        "term_id": first.section.term_id,
                        "term_name": first.section.term.name,
                        "weekday": first.section.weekday,
                        "start_time": overlap_start,
                        "end_time": overlap_end,
                        "message": "两门已选课程存在时间重叠",
                        "first_enrollment_id": first.id,
                        "first_section_id": first.section_id,
                        "first_course_code": first.section.course.code,
                        "first_course_name": first.section.course.name,
                        "first_section_name": first.section.name,
                        "first_teacher_name": first_teacher_profile.real_name if first_teacher_profile and first_teacher_profile.real_name else first.section.teacher.username,
                        "first_location": first.section.location,
                        "second_enrollment_id": second.id,
                        "second_section_id": second.section_id,
                        "second_course_code": second.section.course.code,
                        "second_course_name": second.section.course.name,
                        "second_section_name": second.section.name,
                        "second_teacher_name": second_teacher_profile.real_name if second_teacher_profile and second_teacher_profile.real_name else second.section.teacher.username,
                        "second_location": second.section.location,
                    }
                )

        return Response(ConflictSerializer(conflicts, many=True).data)


class TeacherSectionListView(TeacherOrAdminGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.ensure_teacher_or_admin(request)
        if denied:
            return denied

        queryset = Section.objects.select_related("term", "course", "teacher", "teacher__profile").annotate(
            enrolled_count=Count("enrollments", filter=Q(enrollments__status=Enrollment.STATUS_ENROLLED))
        )

        if not request.user.is_superuser and ensure_user_profile(request.user).role == UserProfile.ROLE_TEACHER:
            queryset = queryset.filter(teacher=request.user)

        term_id = request.query_params.get("term_id")
        if term_id:
            queryset = queryset.filter(term_id=term_id)

        data = [
            {
                "id": section.id,
                "term_id": section.term_id,
                "term_name": section.term.name,
                "course_id": section.course_id,
                "course_code": section.course.code,
                "course_name": section.course.name,
                "name": section.name,
                "teacher_id": section.teacher_id,
                "teacher_name": section.teacher.profile.real_name if getattr(section.teacher, "profile", None) and section.teacher.profile.real_name else section.teacher.username,
                "capacity": section.capacity,
                "enrolled_count": section.enrolled_count,
                "weekday": section.weekday,
                "start_time": section.start_time,
                "end_time": section.end_time,
                "location": section.location,
            }
            for section in queryset.order_by("id")
        ]
        return Response(data)


class TeacherRosterView(TeacherOrAdminGuardMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, section_id):
        denied = self.ensure_teacher_or_admin(request)
        if denied:
            return denied

        section = get_object_or_404(
            Section.objects.select_related("teacher", "teacher__profile", "course", "term"),
            pk=section_id,
        )

        if (
            not request.user.is_superuser
            and ensure_user_profile(request.user).role == UserProfile.ROLE_TEACHER
            and section.teacher_id != request.user.id
        ):
            return error_response("FORBIDDEN", "你只能查看自己所授课班级的名单", status.HTTP_403_FORBIDDEN)

        queryset = Enrollment.objects.select_related(
            "student",
            "student__profile",
            "section",
            "section__course",
            "round",
        ).filter(
            section=section,
            status=Enrollment.STATUS_ENROLLED,
        ).order_by("id")
        return Response(EnrollmentSerializer(queryset, many=True).data)
