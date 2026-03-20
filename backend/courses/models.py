from django.contrib.auth.models import User
from django.db import models


class Course(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    credits = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Section(models.Model):
    WEEKDAY_CHOICES = [
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    ]

    term = models.ForeignKey("rounds.Term", on_delete=models.CASCADE, related_name="sections")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name="teaching_sections")
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=0)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sections"
        ordering = ["-id"]
        unique_together = [("term", "course", "name")]
        indexes = [
            models.Index(fields=["term", "course"], name="section_term_course_idx"),
            models.Index(fields=["term", "teacher"], name="section_term_teacher_idx"),
            models.Index(fields=["term", "weekday", "start_time"], name="section_term_schedule_idx"),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.name}"
