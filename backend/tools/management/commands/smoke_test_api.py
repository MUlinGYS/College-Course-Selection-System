# 执行核心接口冒烟测试，快速验证管理员、教师、学生主流程是否正常。
import json

from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from courses.models import Section
from enrollments.models import Enrollment
from rounds.models import Round


class Command(BaseCommand):
    help = "Run a repeatable API smoke test for admin, student, and teacher flows."

    def handle(self, *args, **options):
        admin = self._login("root", "Root@123456")
        self._expect_status(admin.get("/api/me", format="json"), 200, "管理员获取个人信息")
        self._expect_status(admin.get("/api/terms", format="json"), 200, "管理员获取学期列表")
        self._expect_status(admin.get("/api/rounds", format="json"), 200, "管理员获取轮次列表")
        self._expect_status(admin.get("/api/courses", format="json"), 200, "管理员获取课程列表")
        self._expect_status(admin.get("/api/sections", format="json"), 200, "管理员获取班级列表")
        self._expect_status(admin.get("/api/enrollments", format="json"), 200, "管理员获取选课记录")

        student = self._login("zhang_xiaoming", "Student@123456")
        self._expect_status(student.get("/api/me", format="json"), 200, "学生获取个人信息")
        self._expect_status(student.get("/api/my/enrollments", format="json"), 200, "学生获取我的已选")
        self._expect_status(student.get("/api/my/conflicts", format="json"), 200, "学生获取冲突检查结果")
        self._expect_status(student.get("/api/my/timetable", format="json"), 200, "学生获取我的课表")

        current_round = Round.objects.filter(enabled=True, target_scope=Round.SCOPE_STUDENT).order_by("id").first()
        if not current_round:
            raise CommandError("没有找到启用中的学生轮次，无法执行学生选课测试。")

        try:
            conflict_section = Section.objects.get(course__code="DB202", round=current_round)
            success_section = Section.objects.get(course__code="MA203", round=current_round)
        except Section.DoesNotExist as exc:
            raise CommandError(f"冒烟测试缺少轮次绑定班级：{exc}") from exc

        existing_success = Enrollment.objects.filter(
            student__username="zhang_xiaoming",
            round=current_round,
            section=success_section,
        ).first()
        if existing_success and existing_success.status == Enrollment.STATUS_ENROLLED:
            existing_success.status = Enrollment.STATUS_DROPPED
            existing_success.save(update_fields=["status", "updated_at"])

        conflict_response = student.post(
            "/api/enrollments",
            {"round_id": current_round.id, "section_id": conflict_section.id},
            format="json",
        )
        self._expect_status(conflict_response, 400, "学生时间冲突校验")
        self._expect_json_field(conflict_response, "code", "TIME_CONFLICT", "学生时间冲突错误码")

        enroll_response = student.post(
            "/api/enrollments",
            {"round_id": current_round.id, "section_id": success_section.id},
            format="json",
        )
        self._expect_status(enroll_response, 201, "学生成功选课")
        enrollment_id = enroll_response.json()["id"]

        drop_response = student.delete(f"/api/enrollments/{enrollment_id}", format="json")
        self._expect_status(drop_response, 200, "学生成功退课")

        teacher = self._login("wang_li_teacher", "Teacher@123456")
        sections_response = teacher.get("/api/teacher/sections", format="json")
        self._expect_status(sections_response, 200, "教师获取我的班级")
        sections = sections_response.json()
        if not sections:
            raise CommandError("教师班级列表为空，无法继续名单测试。")

        roster_section_id = next((item["id"] for item in sections if item.get("enrolled_count", 0) > 0), sections[0]["id"])
        roster_response = teacher.get(f"/api/teacher/sections/{roster_section_id}/roster", format="json")
        self._expect_status(roster_response, 200, "教师获取班级名单")

        self.stdout.write(self.style.SUCCESS("API 冒烟测试通过。"))

    def _login(self, username, password):
        client = APIClient(HTTP_HOST="localhost")
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )
        self._expect_status(response, 200, f"{username} 登录")
        token = response.json()["access_token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def _expect_status(self, response, expected, label):
        if response.status_code != expected:
            body = response.content.decode("utf-8", errors="ignore")
            raise CommandError(f"{label}失败：期望 {expected}，实际 {response.status_code}，响应：{body}")
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))

    def _expect_json_field(self, response, field, expected, label):
        data = response.json()
        if data.get(field) != expected:
            raise CommandError(
                f"{label}失败：期望 {field}={expected}，实际 {field}={data.get(field)}，响应：{json.dumps(data, ensure_ascii=False)}"
            )
        self.stdout.write(self.style.SUCCESS(f"{label}通过"))
