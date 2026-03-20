# 执行项目验收级接口自检，覆盖权限、满员、轮次关闭、容量恢复与认证闭环。
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from rest_framework.test import APIClient

from core.utils import ensure_user_profile
from courses.models import Course, Section
from enrollments.models import Enrollment
from rounds.models import Round, Term
from users.models import UserProfile


class Command(BaseCommand):
    help = "Run acceptance-level API checks for permission, enrollment edge cases, and auth flows."

    def handle(self, *args, **options):
        context = self._prepare_acceptance_context()

        self._verify_auth_refresh_and_logout()
        self._verify_permissions()
        self._verify_round_closed(context)
        self._verify_full_and_capacity_recovery(context)

        self.stdout.write(self.style.SUCCESS("验收级接口自检通过。"))

    def _prepare_acceptance_context(self):
        now = timezone.now()
        term, _ = Term.objects.update_or_create(
            name="2026-验收测试学期",
            defaults={
                "start_date": date(2026, 3, 1),
                "end_date": date(2026, 7, 31),
            },
        )

        teacher = self._upsert_user(
            username="accept_teacher",
            password="Accept@123456",
            email="accept.teacher@demo.edu",
            role=UserProfile.ROLE_TEACHER,
            real_name="验收教师",
            teacher_no="AC-T-0001",
            department="验收测试组",
        )
        student_one = self._upsert_user(
            username="accept_student_one",
            password="Accept@123456",
            email="accept.student.one@demo.edu",
            role=UserProfile.ROLE_STUDENT,
            real_name="验收学生一",
            student_no="AC-S-0001",
            department="验收测试组",
        )
        student_two = self._upsert_user(
            username="accept_student_two",
            password="Accept@123456",
            email="accept.student.two@demo.edu",
            role=UserProfile.ROLE_STUDENT,
            real_name="验收学生二",
            student_no="AC-S-0002",
            department="验收测试组",
        )

        full_course, _ = Course.objects.update_or_create(
            code="ACC201",
            defaults={
                "name": "验收测试课程-容量恢复",
                "credits": 1,
                "description": "用于验证满员、退课与容量恢复。",
            },
        )
        closed_course, _ = Course.objects.update_or_create(
            code="ACC202",
            defaults={
                "name": "验收测试课程-轮次关闭",
                "credits": 1,
                "description": "用于验证轮次关闭时的选课拦截。",
            },
        )

        open_round, _ = Round.objects.update_or_create(
            term=term,
            name="验收开放轮次",
            defaults={
                "start_at": now - timedelta(days=1),
                "end_at": now + timedelta(days=7),
                "target_scope": Round.SCOPE_STUDENT,
                "max_courses": 3,
                "allow_drop": True,
                "enabled": True,
            },
        )
        closed_round, _ = Round.objects.update_or_create(
            term=term,
            name="验收关闭轮次",
            defaults={
                "start_at": now - timedelta(days=10),
                "end_at": now - timedelta(days=2),
                "target_scope": Round.SCOPE_STUDENT,
                "max_courses": 3,
                "allow_drop": True,
                "enabled": True,
            },
        )

        full_section, _ = Section.objects.update_or_create(
            term=term,
            course=full_course,
            name="1班",
            defaults={
                "teacher": teacher,
                "capacity": 1,
                "weekday": 5,
                "start_time": time(8, 0),
                "end_time": time(9, 40),
                "location": "验收教室 A-101",
            },
        )
        closed_section, _ = Section.objects.update_or_create(
            term=term,
            course=closed_course,
            name="1班",
            defaults={
                "teacher": teacher,
                "capacity": 10,
                "weekday": 5,
                "start_time": time(10, 10),
                "end_time": time(11, 50),
                "location": "验收教室 A-102",
            },
        )

        Enrollment.objects.filter(
            student__in=[student_one, student_two],
            round__in=[open_round, closed_round],
            section__in=[full_section, closed_section],
        ).delete()

        return {
            "teacher": teacher,
            "student_one": student_one,
            "student_two": student_two,
            "open_round": open_round,
            "closed_round": closed_round,
            "full_section": full_section,
            "closed_section": closed_section,
        }

    def _verify_auth_refresh_and_logout(self):
        client = APIClient(HTTP_HOST="localhost")
        login_response = client.post(
            "/api/auth/login/",
            {"username": "root", "password": "Root@123456"},
            format="json",
        )
        self._expect_status(login_response, 200, "认证闭环-管理员登录")

        payload = login_response.json()
        refresh_response = client.post(
            "/api/auth/refresh/",
            {"refresh": payload["refresh_token"], "refresh_token": payload["refresh_token"]},
            format="json",
        )
        self._expect_status(refresh_response, 200, "认证闭环-刷新令牌")
        self._expect_json_has_key(refresh_response, "access_token", "认证闭环-刷新返回 access_token")

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {payload['access_token']}")
        logout_response = client.post(
            "/api/auth/logout/",
            {"refresh_token": payload["refresh_token"]},
            format="json",
        )
        self._expect_status(logout_response, 200, "认证闭环-退出登录")
        self._expect_json_field(logout_response, "ok", True, "认证闭环-退出返回 ok")

    def _verify_permissions(self):
        student = self._login("zhang_xiaoming", "Student@123456")
        teacher = self._login("wang_li_teacher", "Teacher@123456")

        self._expect_status(student.get("/api/enrollments", format="json"), 403, "权限-学生访问管理员选课记录")
        self._expect_status(student.get("/api/teacher/sections", format="json"), 403, "权限-学生访问教师班级列表")
        self._expect_status(teacher.get("/api/users", format="json"), 403, "权限-教师访问管理员用户列表")
        self._expect_status(teacher.post("/api/enrollments", {"round_id": 1, "section_id": 1}, format="json"), 403, "权限-教师执行学生选课")

    def _verify_round_closed(self, context):
        student = self._login("accept_student_one", "Accept@123456")
        response = student.post(
            "/api/enrollments",
            {"round_id": context["closed_round"].id, "section_id": context["closed_section"].id},
            format="json",
        )
        self._expect_status(response, 400, "边界-关闭轮次拒绝选课")
        self._expect_json_field(response, "code", "ROUND_CLOSED", "边界-关闭轮次错误码")

    def _verify_full_and_capacity_recovery(self, context):
        student_one = self._login("accept_student_one", "Accept@123456")
        student_two = self._login("accept_student_two", "Accept@123456")
        round_id = context["open_round"].id
        section_id = context["full_section"].id

        enroll_one = student_one.post(
            "/api/enrollments",
            {"round_id": round_id, "section_id": section_id},
            format="json",
        )
        self._expect_status(enroll_one, 201, "边界-第一位学生成功选课")
        enrollment_id = enroll_one.json()["id"]

        full_response = student_two.post(
            "/api/enrollments",
            {"round_id": round_id, "section_id": section_id},
            format="json",
        )
        self._expect_status(full_response, 400, "边界-班级满员时拒绝第二次选课")
        self._expect_json_field(full_response, "code", "FULL", "边界-满员错误码")

        timetable_before_drop = student_one.get("/api/my/timetable", format="json")
        self._expect_status(timetable_before_drop, 200, "边界-退课前获取课表")
        self._expect_timetable_contains(timetable_before_drop.json(), section_id, True, "边界-退课前课表包含课程")

        drop_response = student_one.delete(f"/api/enrollments/{enrollment_id}", format="json")
        self._expect_status(drop_response, 200, "边界-退课成功")

        timetable_after_drop = student_one.get("/api/my/timetable", format="json")
        self._expect_status(timetable_after_drop, 200, "边界-退课后获取课表")
        self._expect_timetable_contains(timetable_after_drop.json(), section_id, False, "边界-退课后课表已刷新")

        retry_response = student_two.post(
            "/api/enrollments",
            {"round_id": round_id, "section_id": section_id},
            format="json",
        )
        self._expect_status(retry_response, 201, "边界-容量恢复后第二位学生可选课")

        cleanup_enrollment_id = retry_response.json()["id"]
        cleanup_drop = student_two.delete(f"/api/enrollments/{cleanup_enrollment_id}", format="json")
        self._expect_status(cleanup_drop, 200, "边界-清理验收测试选课记录")

    def _upsert_user(self, *, username, password, email, role, real_name, student_no="", teacher_no="", department=""):
        user, _ = User.objects.get_or_create(username=username)
        user.email = email
        user.is_active = True
        user.is_staff = role == UserProfile.ROLE_ADMIN
        user.is_superuser = False
        user.set_password(password)
        user.save()

        profile = ensure_user_profile(user)
        profile.role = role
        profile.real_name = real_name
        profile.student_no = student_no or None
        profile.teacher_no = teacher_no or None
        profile.department = department
        profile.save()
        return user

    def _login(self, username, password):
        client = APIClient(HTTP_HOST="localhost")
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        self._expect_status(response, 200, f"{username} 登录")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
        return client

    def _expect_status(self, response, expected, label):
        if response.status_code != expected:
            body = response.content.decode("utf-8", errors="ignore")
            raise CommandError(f"{label}失败：期望 {expected}，实际 {response.status_code}，响应：{body}")
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))

    def _expect_json_field(self, response, field, expected, label):
        data = response.json()
        if data.get(field) != expected:
            raise CommandError(f"{label}失败：期望 {field}={expected}，实际 {field}={data.get(field)}，响应：{data}")
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))

    def _expect_json_has_key(self, response, field, label):
        data = response.json()
        if field not in data:
            raise CommandError(f"{label}失败：响应中缺少字段 {field}，响应：{data}")
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))

    def _expect_timetable_contains(self, timetable, section_id, expected, label):
        found = any(item.get("section_id") == section_id for item in timetable)
        if found != expected:
            raise CommandError(f"{label}失败：期望是否包含 section_id={section_id} 为 {expected}，实际 {found}")
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))
