# 对 POST /api/enrollments 执行并发压测，验证选课接口的稳定性与承载能力。
import json
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.utils import ensure_user_profile
from courses.models import Course, Section
from enrollments.models import Enrollment
from rounds.models import Round, Term
from users.models import UserProfile


class Command(BaseCommand):
    help = "Run progressive concurrent load testing against POST /api/enrollments."

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default="http://127.0.0.1:8000")
        parser.add_argument("--levels", default="10,20,50,100,150,200")
        parser.add_argument("--user-count", type=int, default=220)
        parser.add_argument("--timeout", type=float, default=8.0)
        parser.add_argument("--password", default="LoadTest@123456")

    def handle(self, *args, **options):
        base_url = options["base_url"].rstrip("/")
        levels = self._parse_levels(options["levels"])
        user_count = options["user_count"]
        timeout = options["timeout"]
        password = options["password"]

        if max(levels) > user_count:
            raise CommandError(f"并发档位最大值 {max(levels)} 不能大于测试用户数 {user_count}。")

        self._assert_server_is_alive(base_url)
        context = self._prepare_test_data(user_count=user_count, password=password)

        self.stdout.write(self.style.SUCCESS("压测数据准备完成。"))
        self.stdout.write(
            f"目标轮次：{context['round'].name}，目标班级：{context['section'].course.code} / {context['section'].name}，"
            f"测试用户数：{len(context['students'])}"
        )

        results = []
        for level in levels:
            result = self._run_single_level(
                base_url=base_url,
                round_id=context["round"].id,
                section_id=context["section"].id,
                students=context["students"][:level],
                password=password,
                timeout=timeout,
            )
            results.append(result)
            self.stdout.write(self._format_result(result))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("压测完成，汇总如下："))
        self.stdout.write(json.dumps(results, ensure_ascii=False, indent=2))

    def _assert_server_is_alive(self, base_url):
        try:
            response = requests.get(f"{base_url}/api/health/", timeout=3)
        except requests.RequestException as exc:
            raise CommandError(f"无法连接后端服务：{exc}") from exc

        if response.status_code != 200:
            raise CommandError(f"后端服务不可用：{response.status_code} {response.text}")

    def _parse_levels(self, raw_levels):
        try:
            levels = [int(item.strip()) for item in raw_levels.split(",") if item.strip()]
        except ValueError as exc:
            raise CommandError(f"并发档位格式错误：{raw_levels}") from exc

        if not levels:
            raise CommandError("至少要提供一个并发档位。")

        return sorted(set(levels))

    def _prepare_test_data(self, *, user_count, password):
        now = timezone.now()
        term, _ = Term.objects.update_or_create(
            name="2026-压测学期",
            defaults={
                "start_date": date(2026, 3, 1),
                "end_date": date(2026, 7, 31),
            },
        )

        teacher = self._upsert_user(
            username="load_test_teacher",
            password=password,
            email="load.teacher@demo.edu",
            role=UserProfile.ROLE_TEACHER,
            real_name="压测教师",
            teacher_no="LT-T-0001",
            department="性能测试组",
        )

        course, _ = Course.objects.update_or_create(
            code="LOAD101",
            defaults={
                "name": "高并发选课压测课程",
                "credits": 1,
                "description": "用于验证 /api/enrollments 并发保护效果的专用课程。",
            },
        )

        section, _ = Section.objects.update_or_create(
            term=term,
            course=course,
            name="压测班",
            defaults={
                "teacher": teacher,
                "capacity": max(user_count * 2, 500),
                "weekday": 6,
                "start_time": "19:00",
                "end_time": "20:40",
                "location": "性能测试教室",
            },
        )

        round_instance, _ = Round.objects.update_or_create(
            term=term,
            name="并发压测轮次",
            defaults={
                "start_at": now - timedelta(hours=1),
                "end_at": now + timedelta(hours=6),
                "target_scope": Round.SCOPE_STUDENT,
                "max_courses": 1,
                "allow_drop": True,
                "enabled": True,
            },
        )

        students = []
        for index in range(1, user_count + 1):
            username = f"load_student_{index:04d}"
            student = self._upsert_user(
                username=username,
                password=password,
                email=f"{username}@demo.edu",
                role=UserProfile.ROLE_STUDENT,
                real_name=f"压测学生{index:04d}",
                student_no=f"LT-S-{index:04d}",
                department="性能测试组",
            )
            students.append(student)

        Enrollment.objects.filter(section=section).delete()
        Enrollment.objects.filter(student__in=students, section__term=term).delete()

        return {
            "term": term,
            "teacher": teacher,
            "course": course,
            "section": section,
            "round": round_instance,
            "students": students,
        }

    def _upsert_user(self, *, username, password, email, role, real_name, student_no="", teacher_no="", department=""):
        user, _ = User.objects.get_or_create(username=username)
        user.email = email
        user.is_active = True
        user.is_staff = role == UserProfile.ROLE_ADMIN
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

    def _run_single_level(self, *, base_url, round_id, section_id, students, password, timeout):
        student_ids = [student.id for student in students]
        Enrollment.objects.filter(student_id__in=student_ids, round_id=round_id, section_id=section_id).delete()

        tokens = {}
        for student in students:
            response = requests.post(
                f"{base_url}/api/auth/login/",
                json={"username": student.username, "password": password},
                timeout=timeout,
            )
            if response.status_code != 200:
                raise CommandError(f"测试账号登录失败：{student.username} => {response.status_code} {response.text}")
            tokens[student.id] = response.json()["access_token"]

        start_event = threading.Event()
        wall_start = time.perf_counter()
        results = []

        with ThreadPoolExecutor(max_workers=len(students)) as executor:
            futures = [
                executor.submit(
                    self._submit_enrollment,
                    start_event,
                    base_url,
                    tokens[student.id],
                    round_id,
                    section_id,
                    timeout,
                )
                for student in students
            ]
            start_event.set()
            for future in as_completed(futures):
                results.append(future.result())

        wall_duration = time.perf_counter() - wall_start
        status_counter = {}
        code_counter = {}
        latencies = []
        success_count = 0

        for item in results:
            status_key = str(item["status"])
            status_counter[status_key] = status_counter.get(status_key, 0) + 1
            if item["code"]:
                code_counter[item["code"]] = code_counter.get(item["code"], 0) + 1
            if item["latency_ms"] is not None:
                latencies.append(item["latency_ms"])
            if item["status"] == 201:
                success_count += 1

        latencies.sort()
        return {
            "concurrency": len(students),
            "success_count": success_count,
            "success_rate": round(success_count / len(students) * 100, 2),
            "wall_time_s": round(wall_duration, 3),
            "throughput_rps": round(len(students) / wall_duration, 2) if wall_duration else None,
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
            "p50_latency_ms": self._percentile(latencies, 50),
            "p95_latency_ms": self._percentile(latencies, 95),
            "max_latency_ms": round(max(latencies), 2) if latencies else None,
            "status_counter": status_counter,
            "error_code_counter": code_counter,
        }

    def _submit_enrollment(self, start_event, base_url, token, round_id, section_id, timeout):
        start_event.wait()
        started = time.perf_counter()
        try:
            response = requests.post(
                f"{base_url}/api/enrollments",
                json={"round_id": round_id, "section_id": section_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            payload = {}
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text}
            return {
                "status": response.status_code,
                "code": payload.get("code"),
                "latency_ms": elapsed_ms,
            }
        except requests.RequestException as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            return {
                "status": "REQUEST_ERROR",
                "code": exc.__class__.__name__,
                "latency_ms": elapsed_ms,
            }

    def _percentile(self, values, percentile):
        if not values:
            return None
        if len(values) == 1:
            return round(values[0], 2)

        index = round((percentile / 100) * (len(values) - 1))
        return round(values[index], 2)

    def _format_result(self, result):
        return (
            f"[并发 {result['concurrency']}] "
            f"成功率 {result['success_rate']}% | "
            f"吞吐 {result['throughput_rps']} req/s | "
            f"平均 {result['avg_latency_ms']} ms | "
            f"P95 {result['p95_latency_ms']} ms | "
            f"状态 {result['status_counter']} | "
            f"错误码 {result['error_code_counter']}"
        )
