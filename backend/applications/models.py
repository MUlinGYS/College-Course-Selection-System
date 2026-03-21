from django.contrib.auth.models import User
from django.db import models


class CourseApplication(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    WEEKDAY_CHOICES = [
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    ]

    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name="course_applications")
    term = models.ForeignKey("rounds.Term", on_delete=models.CASCADE, related_name="course_applications")
    round = models.ForeignKey(
        "rounds.Round",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="course_applications",
    )
    course_code = models.CharField(max_length=50)
    course_name = models.CharField(max_length=200)
    credits = models.PositiveIntegerField(default=0)
    course_description = models.TextField(blank=True, default="")
    section_name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=0)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True, default="")
    apply_note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    review_note = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviewed_course_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    linked_course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="course_applications",
    )
    linked_section = models.ForeignKey(
        "courses.Section",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="course_applications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_applications"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["teacher", "status"], name="app_teacher_status_idx"),
            models.Index(fields=["term", "status"], name="app_term_status_idx"),
            models.Index(fields=["round", "status"], name="app_round_status_idx"),
            models.Index(fields=["status", "created_at"], name="app_status_created_idx"),
        ]

    def __str__(self):
        return f"{self.teacher.username} - {self.course_code} - {self.section_name}"
