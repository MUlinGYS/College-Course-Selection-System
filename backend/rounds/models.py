from django.db import models


class Term(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "terms"
        ordering = ["-id"]

    def __str__(self):
        return self.name


class Round(models.Model):
    SCOPE_ALL = "all"
    SCOPE_STUDENT = "student"
    SCOPE_TEACHER = "teacher"

    TARGET_SCOPE_CHOICES = [
        (SCOPE_ALL, "All"),
        (SCOPE_STUDENT, "Student"),
        (SCOPE_TEACHER, "Teacher"),
    ]

    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="rounds")
    name = models.CharField(max_length=100)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    target_scope = models.CharField(max_length=20, choices=TARGET_SCOPE_CHOICES, default=SCOPE_STUDENT)
    max_courses = models.PositiveIntegerField(default=0)
    allow_drop = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rounds"
        ordering = ["-id"]
        unique_together = [("term", "name")]
        indexes = [
            models.Index(fields=["term", "enabled"], name="round_term_enabled_idx"),
            models.Index(fields=["enabled", "start_at", "end_at"], name="round_enabled_window_idx"),
        ]

    def __str__(self):
        return f"{self.term.name} - {self.name}"
