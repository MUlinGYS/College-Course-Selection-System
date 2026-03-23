# 批量生成更丰富的用户、课程、班级和选课记录，用于正式演示与联调。
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.utils import ensure_user_profile
from courses.models import Course, Section
from enrollments.models import Enrollment
from rounds.models import Round, Term
from users.models import UserProfile


COURSE_CATALOG = [
    ("CS201", "数据结构", 4, "面向程序设计与算法分析的核心课程。"),
    ("CS202", "计算机网络", 3, "介绍网络分层模型、协议与应用。"),
    ("CS203", "操作系统", 4, "覆盖进程、线程、内存与文件系统。"),
    ("CS204", "软件工程", 3, "讲解需求分析、设计、测试与维护。"),
    ("CS205", "Web 应用开发", 3, "面向前后端分离场景的开发实践。"),
    ("CS206", "面向对象程序设计", 3, "强化类、继承、多态等编程思想。"),
    ("CS207", "Python 高级开发", 3, "聚焦 Python 工程化与框架实战。"),
    ("CS208", "Java 程序设计", 3, "面向企业开发的 Java 基础课程。"),
    ("CS209", "算法设计与分析", 4, "常见算法思想与复杂度分析。"),
    ("CS210", "人工智能导论", 3, "介绍 AI 基础概念与典型应用。"),
    ("DS301", "数据挖掘", 3, "面向数据分析与模式发现。"),
    ("DS302", "机器学习基础", 4, "监督学习、模型评估与常见算法。"),
    ("DS303", "大数据技术导论", 3, "讲解分布式存储与计算框架。"),
    ("DS304", "统计学习方法", 3, "结合统计理论与机器学习方法。"),
    ("MA301", "高等数学", 4, "函数、极限、导数与积分。"),
    ("MA302", "线性代数", 3, "矩阵、向量空间与线性变换。"),
    ("MA303", "概率论与数理统计", 3, "概率分布、估计与假设检验。"),
    ("EE201", "数字逻辑", 3, "逻辑代数、组合逻辑与时序逻辑。"),
    ("EE202", "计算机组成原理", 4, "CPU、存储器与指令系统。"),
    ("IS201", "信息系统分析与设计", 3, "面向业务系统的分析与建模。"),
    ("IS202", "数据库系统实践", 3, "数据库建模、索引与性能优化。"),
    ("MG201", "项目管理", 2, "项目计划、执行、风险与沟通。"),
    ("EN201", "大学英语拓展", 2, "综合阅读、写作与表达训练。"),
    ("PE201", "体育选修", 1, "常规体育训练与身体素质提升。"),
]

TEACHER_PROFILES = [
    ("zhao_jing_teacher", "赵静", "T2026101", "计算机学院"),
    ("sun_bo_teacher", "孙博", "T2026102", "计算机学院"),
    ("he_qing_teacher", "何青", "软件学院"),
    ("zhou_nan_teacher", "周楠", "软件学院"),
    ("liang_yu_teacher", "梁宇", "数据科学学院"),
    ("guo_min_teacher", "郭敏", "数据科学学院"),
    ("deng_fei_teacher", "邓飞", "人工智能学院"),
    ("yan_lu_teacher", "闫璐", "人工智能学院"),
    ("qian_hui_teacher", "钱慧", "数学学院"),
    ("wu_jie_teacher", "吴杰", "数学学院"),
    ("feng_xin_teacher", "冯鑫", "信息工程学院"),
    ("cao_ning_teacher", "曹宁", "信息工程学院"),
]

TIME_SLOTS = [
    (1, time(8, 0), time(9, 40)),
    (1, time(10, 10), time(11, 50)),
    (1, time(14, 0), time(15, 40)),
    (1, time(16, 10), time(17, 50)),
    (2, time(8, 0), time(9, 40)),
    (2, time(10, 10), time(11, 50)),
    (2, time(14, 0), time(15, 40)),
    (2, time(16, 10), time(17, 50)),
    (3, time(8, 0), time(9, 40)),
    (3, time(10, 10), time(11, 50)),
    (3, time(14, 0), time(15, 40)),
    (3, time(16, 10), time(17, 50)),
    (4, time(8, 0), time(9, 40)),
    (4, time(10, 10), time(11, 50)),
    (4, time(14, 0), time(15, 40)),
    (4, time(16, 10), time(17, 50)),
    (5, time(8, 0), time(9, 40)),
    (5, time(10, 10), time(11, 50)),
    (5, time(14, 0), time(15, 40)),
    (5, time(16, 10), time(17, 50)),
]

LOCATIONS = [
    "博学楼 A-201",
    "博学楼 A-302",
    "明理楼 B-105",
    "明理楼 B-208",
    "求实楼 C-110",
    "求实楼 C-306",
    "致远楼 D-203",
    "致远楼 D-402",
]


class Command(BaseCommand):
    help = "Seed richer demo data for users, courses, sections, and enrollments."

    @transaction.atomic
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

        current_round = self._upsert_round(
            term=current_term,
            name="第一轮选课",
            start_at=now - timedelta(days=10),
            end_at=now + timedelta(days=25),
            target_scope=Round.SCOPE_STUDENT,
            max_courses=2,
            allow_drop=True,
            enabled=True,
        )
        next_round = self._upsert_round(
            term=next_term,
            name="下学期预设轮次",
            start_at=now + timedelta(days=90),
            end_at=now + timedelta(days=120),
            target_scope=Round.SCOPE_STUDENT,
            max_courses=3,
            allow_drop=True,
            enabled=True,
        )

        teachers = self._ensure_teachers()
        courses = self._ensure_courses()
        current_sections = self._ensure_sections(current_term, current_round, teachers, courses, term_offset=0)
        next_sections = self._ensure_sections(next_term, next_round, teachers, courses, term_offset=7)
        students = list(
            User.objects.filter(profile__role=UserProfile.ROLE_STUDENT)
            .exclude(username__in=["zhang_xiaoming", "li_hua_student"])
            .order_by("id")[:300]
        )

        touched = self._seed_enrollments(
            students=students,
            current_round=current_round,
            next_round=next_round,
            current_sections=current_sections,
            next_sections=next_sections,
        )

        summary = {
            "users": User.objects.count(),
            "teachers": User.objects.filter(profile__role=UserProfile.ROLE_TEACHER).count(),
            "students": User.objects.filter(profile__role=UserProfile.ROLE_STUDENT).count(),
            "courses": Course.objects.count(),
            "sections": Section.objects.count(),
            "enrollments": Enrollment.objects.count(),
        }

        self.stdout.write(self.style.SUCCESS("富化演示数据写入完成。"))
        self.stdout.write(f"本轮处理选课记录：{touched} 条")
        self.stdout.write(f"当前数据总量：{summary}")

    def _ensure_teachers(self):
        existing = list(User.objects.filter(profile__role=UserProfile.ROLE_TEACHER).order_by("id"))
        teachers = existing[:]

        for profile_data in TEACHER_PROFILES:
            username, real_name, teacher_no, department = profile_data
            user, _ = User.objects.get_or_create(username=username)
            user.email = f"{username}@demo.edu"
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.set_password("Teacher@123456")
            user.save()

            profile = ensure_user_profile(user)
            profile.role = UserProfile.ROLE_TEACHER
            profile.real_name = real_name
            profile.teacher_no = teacher_no
            profile.student_no = None
            profile.phone = self._fake_phone(teacher_no[-4:])
            profile.department = department
            profile.save()

            teachers.append(user)

        unique_teachers = []
        seen_ids = set()
        for teacher in teachers:
            if teacher.id in seen_ids:
                continue
            seen_ids.add(teacher.id)
            unique_teachers.append(teacher)
        return unique_teachers

    def _ensure_courses(self):
        courses = []
        for code, name, credits, description in COURSE_CATALOG:
            course, _ = Course.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "credits": credits,
                    "description": description,
                },
            )
            courses.append(course)
        return courses

    def _ensure_sections(self, term, round_instance, teachers, courses, term_offset):
        sections = []
        teacher_count = len(teachers)

        for index, course in enumerate(courses):
            weekday, start_time, end_time = TIME_SLOTS[(index + term_offset) % len(TIME_SLOTS)]
            section, _ = Section.objects.update_or_create(
                round=round_instance,
                course=course,
                name="1班",
                defaults={
                    "term": term,
                    "teacher": teachers[index % teacher_count],
                    "capacity": 80,
                    "weekday": weekday,
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": LOCATIONS[index % len(LOCATIONS)],
                },
            )
            sections.append(section)

            if index < 12:
                weekday, start_time, end_time = TIME_SLOTS[(index + term_offset + 9) % len(TIME_SLOTS)]
                extra_section, _ = Section.objects.update_or_create(
                    round=round_instance,
                    course=course,
                    name="2班",
                    defaults={
                        "term": term,
                        "teacher": teachers[(index + 3) % teacher_count],
                        "capacity": 60,
                        "weekday": weekday,
                        "start_time": start_time,
                        "end_time": end_time,
                        "location": LOCATIONS[(index + 3) % len(LOCATIONS)],
                    },
                )
                sections.append(extra_section)

        return sorted(sections, key=lambda item: item.id)

    def _seed_enrollments(self, *, students, current_round, next_round, current_sections, next_sections):
        touched = 0

        for index, student in enumerate(students):
            current_selected = self._pick_sections(current_sections, seed=index * 2, count=2)
            next_selected = self._pick_sections(next_sections, seed=index * 3, count=3)

            for section in current_selected:
                _, created = Enrollment.objects.update_or_create(
                    student=student,
                    round=current_round,
                    section=section,
                    defaults={"status": Enrollment.STATUS_ENROLLED},
                )
                touched += 1 if created else 0

            for section in next_selected:
                _, created = Enrollment.objects.update_or_create(
                    student=student,
                    round=next_round,
                    section=section,
                    defaults={"status": Enrollment.STATUS_ENROLLED},
                )
                touched += 1 if created else 0

            if index % 5 == 0:
                dropped_section = self._pick_sections(current_sections, seed=index * 5 + 1, count=1, forbidden=current_selected)[0]
                _, created = Enrollment.objects.update_or_create(
                    student=student,
                    round=current_round,
                    section=dropped_section,
                    defaults={"status": Enrollment.STATUS_DROPPED},
                )
                touched += 1 if created else 0

        return touched

    def _pick_sections(self, sections, *, seed, count, forbidden=None):
        picked = []
        used_slots = set()
        forbidden_ids = {item.id for item in (forbidden or [])}

        for offset in range(len(sections)):
            section = sections[(seed + offset) % len(sections)]
            slot_key = (section.weekday, section.start_time, section.end_time)

            if section.id in forbidden_ids:
                continue
            if slot_key in used_slots:
                continue

            picked.append(section)
            used_slots.add(slot_key)
            if len(picked) == count:
                break

        return picked

    def _upsert_term(self, *, name, start_date, end_date):
        term, _ = Term.objects.update_or_create(
            name=name,
            defaults={
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        return term

    def _upsert_round(self, *, term, name, start_at, end_at, target_scope, max_courses, allow_drop, enabled):
        round_instance, _ = Round.objects.update_or_create(
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
        return round_instance

    def _fake_phone(self, suffix):
        return f"138{suffix}".ljust(11, "0")
