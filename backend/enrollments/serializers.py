from rest_framework import serializers

from .models import Enrollment


class EnrollmentWriteSerializer(serializers.Serializer):
    round_id = serializers.IntegerField()
    section_id = serializers.IntegerField()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source="student.id", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    student_name = serializers.SerializerMethodField()
    round_name = serializers.CharField(source="round.name", read_only=True)
    term_id = serializers.IntegerField(source="section.term.id", read_only=True)
    term_name = serializers.CharField(source="section.term.name", read_only=True)
    course_id = serializers.IntegerField(source="section.course.id", read_only=True)
    course_code = serializers.CharField(source="section.course.code", read_only=True)
    course_name = serializers.CharField(source="section.course.name", read_only=True)
    section_id = serializers.IntegerField(source="section.id", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    weekday = serializers.IntegerField(source="section.weekday", read_only=True)
    start_time = serializers.TimeField(source="section.start_time", read_only=True)
    end_time = serializers.TimeField(source="section.end_time", read_only=True)
    location = serializers.CharField(source="section.location", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student_id",
            "student_username",
            "student_name",
            "round",
            "round_name",
            "term_id",
            "term_name",
            "course_id",
            "course_code",
            "course_name",
            "section_id",
            "section_name",
            "teacher_name",
            "weekday",
            "start_time",
            "end_time",
            "location",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_student_name(self, obj) -> str:
        profile = getattr(obj.student, "profile", None)
        return profile.real_name if profile and profile.real_name else obj.student.username

    def get_teacher_name(self, obj) -> str:
        profile = getattr(obj.section.teacher, "profile", None)
        return profile.real_name if profile and profile.real_name else obj.section.teacher.username


class TimetableSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    section_id = serializers.IntegerField()
    section_name = serializers.CharField()
    teacher_name = serializers.CharField()
    weekday = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    location = serializers.CharField()


class ConflictSerializer(serializers.Serializer):
    conflict_key = serializers.CharField()
    term_id = serializers.IntegerField()
    term_name = serializers.CharField()
    weekday = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    message = serializers.CharField()
    first_enrollment_id = serializers.IntegerField()
    first_section_id = serializers.IntegerField()
    first_course_code = serializers.CharField()
    first_course_name = serializers.CharField()
    first_section_name = serializers.CharField()
    first_teacher_name = serializers.CharField()
    first_location = serializers.CharField()
    second_enrollment_id = serializers.IntegerField()
    second_section_id = serializers.IntegerField()
    second_course_code = serializers.CharField()
    second_course_name = serializers.CharField()
    second_section_name = serializers.CharField()
    second_teacher_name = serializers.CharField()
    second_location = serializers.CharField()


class TeacherSectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    term_id = serializers.IntegerField()
    term_name = serializers.CharField()
    round_id = serializers.IntegerField(allow_null=True)
    round_name = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    course_id = serializers.IntegerField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    name = serializers.CharField()
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    capacity = serializers.IntegerField()
    enrolled_count = serializers.IntegerField()
    weekday = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    location = serializers.CharField()
