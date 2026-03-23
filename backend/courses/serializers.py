from django.contrib.auth.models import User
from rest_framework import serializers

from users.models import UserProfile
from .models import Course, Section


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "name", "credits", "description", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class SectionSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source="term.name", read_only=True)
    round_name = serializers.CharField(source="round.name", read_only=True, allow_null=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    teacher_username = serializers.CharField(source="teacher.username", read_only=True)

    class Meta:
        model = Section
        fields = [
            "id",
            "term",
            "term_name",
            "round",
            "round_name",
            "course",
            "course_name",
            "course_code",
            "teacher",
            "teacher_name",
            "teacher_username",
            "name",
            "capacity",
            "weekday",
            "start_time",
            "end_time",
            "location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "term_name",
            "round_name",
            "course_name",
            "course_code",
            "teacher_name",
            "teacher_username",
        ]

    def get_teacher_name(self, obj) -> str:
        profile = getattr(obj.teacher, "profile", None)
        return profile.real_name if profile and profile.real_name else obj.teacher.username

    def validate_teacher(self, teacher: User):
        if teacher.is_superuser:
            return teacher

        profile = getattr(teacher, "profile", None)
        if not profile or profile.role != UserProfile.ROLE_TEACHER:
            raise serializers.ValidationError("授课教师必须是教师角色用户")

        return teacher

    def validate(self, attrs):
        attrs = super().validate(attrs)
        term = attrs.get("term", getattr(self.instance, "term", None))
        round_instance = attrs.get("round", getattr(self.instance, "round", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if not round_instance:
            raise serializers.ValidationError({"round": "必须选择轮次"})

        if term and round_instance.term_id != term.id:
            raise serializers.ValidationError({"round": "所选轮次不属于当前学期"})

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("结束时间必须晚于开始时间")

        return attrs
