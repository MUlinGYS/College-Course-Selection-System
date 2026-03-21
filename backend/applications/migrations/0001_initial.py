from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("courses", "0002_section_indexes"),
        ("rounds", "0002_round_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_code", models.CharField(max_length=50)),
                ("course_name", models.CharField(max_length=200)),
                ("credits", models.PositiveIntegerField(default=0)),
                ("course_description", models.TextField(blank=True, default="")),
                ("section_name", models.CharField(max_length=100)),
                (
                    "capacity",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "weekday",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Monday"),
                            (2, "Tuesday"),
                            (3, "Wednesday"),
                            (4, "Thursday"),
                            (5, "Friday"),
                            (6, "Saturday"),
                            (7, "Sunday"),
                        ]
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("location", models.CharField(blank=True, default="", max_length=100)),
                ("apply_note", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("review_note", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "linked_course",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="course_applications",
                        to="courses.course",
                    ),
                ),
                (
                    "linked_section",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="course_applications",
                        to="courses.section",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reviewed_course_applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="course_applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "term",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course_applications",
                        to="rounds.term",
                    ),
                ),
            ],
            options={
                "db_table": "course_applications",
                "ordering": ["-id"],
            },
        ),
        migrations.AddIndex(
            model_name="courseapplication",
            index=models.Index(fields=["teacher", "status"], name="app_teacher_status_idx"),
        ),
        migrations.AddIndex(
            model_name="courseapplication",
            index=models.Index(fields=["term", "status"], name="app_term_status_idx"),
        ),
        migrations.AddIndex(
            model_name="courseapplication",
            index=models.Index(fields=["status", "created_at"], name="app_status_created_idx"),
        ),
    ]
