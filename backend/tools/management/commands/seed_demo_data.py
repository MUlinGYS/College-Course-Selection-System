# 初始化基础演示数据，用于管理员、教师、学生三角色联调。
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.utils import ensure_user_profile
from courses.models import Course, Section
from enrollments.models import Enrollment
from rounds.models import Round, Term
from users.models import UserProfile


class Command(BaseCommand):
    help = "Seed demo data for admin, student, and teacher integration testing."

    def handle(self, *args, **options):
        now = timezone.now()
        current_term = self._upsert_term(
            name="2025-2026-2",
            start_date=date(2026, 2, 24),
            end_date=date(2026, 7, 5),
        )
        next_term = self._upsert_term(
            name="2026-2027-1",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 15),
        )

        admin_user = self._upsert_user(
            username="root",
            password="Root@123456",
            email="root@demo.edu",
            role=UserProfile.ROLE_ADMIN,
            real_name="系统管理员",
            department="信息中心",
            is_staff=True,
            is_superuser=False,
        )
        teacher_one = self._upsert_user(
            username="wang_li_teacher",
            password="Teacher@123456",
            email="wang.li@demo.edu",
            role=UserProfile.ROLE_TEACHER,
            real_name="王丽",
            teacher_no="T2026001",
            phone="13800000001",
            department="计算机学院",
        )
        teacher_two = self._upsert_user(
            username="liu_ming_teacher",
            password="Teacher@123456",
            email="liu.ming@demo.edu",
            role=UserProfile.ROLE_TEACHER,
            real_name="刘明",
            teacher_no="T2026002",
            phone="13800000002",
            department="数学学院",
        )
        student_one = self._upsert_user(
            username="zhang_xiaoming",
            password="Student@123456",
            email="zhang.xiaoming@demo.edu",
            role=UserProfile.ROLE_STUDENT,
            real_name="张小明",
            student_no="S2026001",
            phone="13900000001",
            department="计算机科学与技术",
        )
        student_two = self._upsert_user(
            username="li_hua_student",
            password="Student@123456",
            email="li.hua@demo.edu",
            role=UserProfile.ROLE_STUDENT,
            real_name="李华",
            student_no="S2026002",
            phone="13900000002",
            department="数据科学与大数据技术",
        )

        round_open = self._upsert_round(
            term=current_term,
            name="第一轮选课",
            start_at=now - timedelta(days=7),
            end_at=now + timedelta(days=21),
            target_scope=Round.SCOPE_STUDENT,
            max_courses=2,
            allow_drop=True,
            enabled=True,
        )
        self._upsert_round(
            term=current_term,
            name="已关闭测试轮次",
            start_at=now - timedelta(days=40),
            end_at=now - timedelta(days=20),
            target_scope=Round.SCOPE_STUDENT,
            max_courses=1,
            allow_drop=False,
            enabled=False,
        )
        self._upsert_round(
            term=next_term,
            name="下学期预设轮次",
            start_at=now + timedelta(days=120),
            end_at=now + timedelta(days=140),
            target_scope=Round.SCOPE_STUDENT,
            max_courses=3,
            allow_drop=True,
            enabled=True,
        )

        course_python = self._upsert_course(
            code="CS101",
            name="Python程序设计",
            credits=3,
            description="面向本科生的 Python 编程基础课程。",
        )
        course_db = self._upsert_course(
            code="DB202",
            name="数据库原理",
            credits=3,
            description="关系数据库、SQL 与事务控制。",
        )
        course_math = self._upsert_course(
            code="MA203",
            name="离散数学",
            credits=4,
            description="集合、关系、图与逻辑基础。",
        )

        section_python = self._upsert_section(
            term=current_term,
            course=course_python,
            teacher=teacher_one,
            name="1班",
            capacity=40,
            weekday=1,
            start_time=time(8, 0),
            end_time=time(9, 40),
            location="博学楼 A-201",
        )
        section_db = self._upsert_section(
            term=current_term,
            course=course_db,
            teacher=teacher_one,
            name="1班",
            capacity=35,
            weekday=1,
            start_time=time(9, 0),
            end_time=time(10, 40),
            location="博学楼 A-302",
        )
        section_math = self._upsert_section(
            term=current_term,
            course=course_math,
            teacher=teacher_two,
            name="1班",
            capacity=45,
            weekday=3,
            start_time=time(14, 0),
            end_time=time(15, 40),
            location="明理楼 B-105",
        )

        self._upsert_enrollment(student_one, round_open, section_python, Enrollment.STATUS_ENROLLED)
        self._upsert_enrollment(student_two, round_open, section_math, Enrollment.STATUS_ENROLLED)
        self._upsert_enrollment(student_two, round_open, section_db, Enrollment.STATUS_DROPPED)

        self.stdout.write(self.style.SUCCESS("演示数据初始化完成。"))
        self.stdout.write("可用账号：")
        self.stdout.write("管理员 root / Root@123456")
        self.stdout.write("教师 wang_li_teacher / Teacher@123456")
        self.stdout.write("教师 liu_ming_teacher / Teacher@123456")
        self.stdout.write("学生 zhang_xiaoming / Student@123456")
        self.stdout.write("学生 li_hua_student / Student@123456")
        self.stdout.write(f"当前开放轮次：{round_open.name}（{current_term.name}）")

    def _upsert_user(
        self,
        *,
        username,
        password,
        email,
        role,
        real_name,
        student_no="",
        teacher_no="",
        phone="",
        department="",
        is_staff=False,
        is_superuser=False,
    ):
        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.is_active = True
        user.is_staff = is_staff or role == UserProfile.ROLE_ADMIN
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()

        profile = ensure_user_profile(user)
        profile.role = role
        profile.real_name = real_name
        profile.student_no = student_no or None
        profile.teacher_no = teacher_no or None
        profile.phone = phone
        profile.department = department
        profile.save()

        self.stdout.write(f"{'创建' if created else '更新'}用户：{username}")
        return user

    def _upsert_term(self, *, name, start_date, end_date):
        term, created = Term.objects.update_or_create(
            name=name,
            defaults={
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        self.stdout.write(f"{'创建' if created else '更新'}学期：{name}")
        return term

    def _upsert_round(self, *, term, name, start_at, end_at, target_scope, max_courses, allow_drop, enabled):
        round_instance, created = Round.objects.update_or_create(
            term=term,
            name=name,
            defaults={
                "start_at": start_at,
                "end_at": end_at,
                "target_scope": target_scope,
                "max_courses": max_courses,
                "allow_drop": allow_drop,
                "enabled": enabled,
            },
        )
        self.stdout.write(f"{'创建' if created else '更新'}轮次：{term.name} / {name}")
        return round_instance

    def _upsert_course(self, *, code, name, credits, description):
        course, created = Course.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "credits": credits,
                "description": description,
            },
        )
        self.stdout.write(f"{'创建' if created else '更新'}课程：{code}")
        return course

    def _upsert_section(self, *, term, course, teacher, name, capacity, weekday, start_time, end_time, location):
        section, created = Section.objects.update_or_create(
            term=term,
            course=course,
            name=name,
            defaults={
                "teacher": teacher,
                "capacity": capacity,
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
            },
        )
        self.stdout.write(f"{'创建' if created else '更新'}班级：{course.code} / {name}")
        return section

    def _upsert_enrollment(self, student, round_instance, section, status_value):
        enrollment, created = Enrollment.objects.update_or_create(
            student=student,
            round=round_instance,
            section=section,
            defaults={"status": status_value},
        )
        self.stdout.write(
            f"{'创建' if created else '更新'}选课记录：{student.username} -> {section.course.code} / {section.name} / {status_value}"
        )
        return enrollment
