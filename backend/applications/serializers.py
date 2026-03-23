from rest_framework import serializers

from courses.models import Course, Section
from courses.serializers import SectionSerializer
from users.models import UserProfile
from .models import CourseApplication


class CourseApplicationSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source="term.name", read_only=True)
    round_name = serializers.CharField(source="round.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    teacher_username = serializers.CharField(source="teacher.username", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    linked_course_code = serializers.CharField(source="linked_course.code", read_only=True)
    linked_course_name = serializers.CharField(source="linked_course.name", read_only=True)
    linked_section_name = serializers.CharField(source="linked_section.name", read_only=True)

    class Meta:
        model = CourseApplication
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "teacher_username",
            "term",
            "term_name",
            "round",
            "round_name",
            "course_code",
            "course_name",
            "credits",
            "course_description",
            "section_name",
            "capacity",
            "weekday",
            "start_time",
            "end_time",
            "location",
            "apply_note",
            "status",
            "review_note",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "linked_course",
            "linked_course_code",
            "linked_course_name",
            "linked_section",
            "linked_section_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "teacher",
            "teacher_name",
            "teacher_username",
            "term_name",
            "round_name",
            "status",
            "review_note",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "linked_course",
            "linked_course_code",
            "linked_course_name",
            "linked_section",
            "linked_section_name",
            "created_at",
            "updated_at",
        ]

    def get_teacher_name(self, obj) -> str:
        profile = getattr(obj.teacher, "profile", None)
        return profile.real_name if profile and profile.real_name else obj.teacher.username

    def get_reviewed_by_name(self, obj) -> str:
        reviewer = getattr(obj, "reviewed_by", None)
        if not reviewer:
            return ""

        profile = getattr(reviewer, "profile", None)
        return profile.real_name if profile and profile.real_name else reviewer.username


class CourseApplicationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseApplication
        fields = [
            "term",
            "round",
            "course_code",
            "course_name",
            "credits",
            "course_description",
            "section_name",
            "capacity",
            "weekday",
            "start_time",
            "end_time",
            "location",
            "apply_note",
        ]

    def validate_course_code(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("课程编号不能为空")
        return value

    def validate_course_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("课程名称不能为空")
        return value

    def validate_section_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("班级名称不能为空")
        return value

    def validate_capacity(self, value):
        if value < 0:
            raise serializers.ValidationError("容量不能小于 0")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        term = attrs.get("term", getattr(self.instance, "term", None))
        round_instance = attrs.get("round", getattr(self.instance, "round", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if not round_instance:
            raise serializers.ValidationError({"round": "必须选择轮次"})

        if term and round_instance and round_instance.term_id != term.id:
            raise serializers.ValidationError({"round": "所选轮次不属于当前学期"})

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("结束时间必须晚于开始时间")

        return attrs


class CourseApplicationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    review_note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        action = attrs.get("action")
        review_note = attrs.get("review_note", "").strip()

        if action == "reject" and not review_note:
            raise serializers.ValidationError({"review_note": "驳回时必须填写审核意见"})

        attrs["review_note"] = review_note
        return attrs


def validate_application_teacher(teacher):
    if teacher.is_superuser:
        return

    profile = getattr(teacher, "profile", None)
    if not profile or profile.role != UserProfile.ROLE_TEACHER:
        raise serializers.ValidationError("申报教师必须是教师角色")


def resolve_course_for_application(application):
    existing_course = Course.objects.filter(code=application.course_code).first()
    if not existing_course:
        return Course.objects.create(
            code=application.course_code,
            name=application.course_name,
            credits=application.credits,
            description=application.course_description,
        )

    mismatch_fields = []
    if existing_course.name != application.course_name:
        mismatch_fields.append("课程名称")
    if existing_course.credits != application.credits:
        mismatch_fields.append("学分")

    if mismatch_fields:
        joined = "、".join(mismatch_fields)
        raise serializers.ValidationError(
            {"message": f"课程编号已存在，且与课程库中的{joined}不一致，请先调整申报信息或维护课程库"}
        )

    return existing_course


def create_section_for_application(application, course):
    if Section.objects.filter(
        round=application.round,
        course=course,
        name=application.section_name,
    ).exists():
        raise serializers.ValidationError({"message": "该轮次下已存在同课程同班级名称的开课记录"})

    serializer = SectionSerializer(
        data={
            "term": application.term_id,
            "round": application.round_id,
            "course": course.id,
            "teacher": application.teacher_id,
            "name": application.section_name,
            "capacity": application.capacity,
            "weekday": application.weekday,
            "start_time": application.start_time,
            "end_time": application.end_time,
            "location": application.location,
        }
    )
    serializer.is_valid(raise_exception=True)
    return serializer.save()
