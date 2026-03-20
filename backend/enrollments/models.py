from django.conf import settings
from django.db import models


class Enrollment(models.Model):
    STATUS_ENROLLED = "enrolled"
    STATUS_DROPPED = "dropped"

    STATUS_CHOICES = [
        (STATUS_ENROLLED, "Enrolled"),
        (STATUS_DROPPED, "Dropped"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    round = models.ForeignKey(
        "rounds.Round",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    section = models.ForeignKey(
        "courses.Section",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENROLLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enrollments"
        ordering = ["-id"]
        unique_together = [("student", "round", "section")]
        indexes = [
            models.Index(fields=["section", "status"], name="enroll_section_status_idx"),
            models.Index(fields=["student", "round", "status"], name="enr_stu_rnd_stat_idx"),
            models.Index(fields=["student", "status"], name="enroll_student_status_idx"),
            models.Index(fields=["round", "status"], name="enroll_round_status_idx"),
        ]

    def __str__(self):
        return f"{self.student.username} -> {self.section_id} ({self.status})"
