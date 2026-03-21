from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from core.utils import ensure_user_profile
from .models import UserProfile


def normalize_optional_value(value):
    return value or None


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "role",
            "real_name",
            "student_no",
            "teacher_no",
            "phone",
            "department",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()
    student_no = serializers.SerializerMethodField()
    teacher_no = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    is_enabled = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "real_name",
            "student_no",
            "teacher_no",
            "phone",
            "department",
            "is_enabled",
            "is_staff",
            "is_superuser",
            "date_joined",
        ]

    def _profile(self, obj):
        return ensure_user_profile(obj)

    def get_role(self, obj) -> str:
        return self._profile(obj).role

    def get_real_name(self, obj) -> str:
        return self._profile(obj).real_name

    def get_student_no(self, obj) -> str:
        return self._profile(obj).student_no

    def get_teacher_no(self, obj) -> str:
        return self._profile(obj).teacher_no

    def get_phone(self, obj) -> str:
        return self._profile(obj).phone

    def get_department(self, obj) -> str:
        return self._profile(obj).department


class AdminUserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        min_length=6,
        error_messages={
            "blank": "密码不能为空",
            "min_length": "密码长度不能少于 6 位",
        },
    )
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    real_name = serializers.CharField(required=False, allow_blank=True, default="")
    student_no = serializers.CharField(required=False, allow_blank=True, default="")
    teacher_no = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    department = serializers.CharField(required=False, allow_blank=True, default="")
    is_enabled = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "role",
            "real_name",
            "student_no",
            "teacher_no",
            "phone",
            "department",
            "is_enabled",
        ]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "创建用户时必须填写密码"})

        role = attrs.get("role")
        student_no = normalize_optional_value(attrs.get("student_no"))
        teacher_no = normalize_optional_value(attrs.get("teacher_no"))
        profile_queryset = UserProfile.objects.all()

        if self.instance:
            profile_queryset = profile_queryset.exclude(user=self.instance)

        if student_no and profile_queryset.filter(student_no=student_no).exists():
            raise serializers.ValidationError({"student_no": "该学号已存在"})

        if teacher_no and profile_queryset.filter(teacher_no=teacher_no).exists():
            raise serializers.ValidationError({"teacher_no": "该工号已存在"})

        if role == UserProfile.ROLE_STUDENT and teacher_no:
            raise serializers.ValidationError({"teacher_no": "学生角色不能填写工号"})

        if role == UserProfile.ROLE_TEACHER and student_no:
            raise serializers.ValidationError({"student_no": "教师角色不能填写学号"})

        return attrs

    def create(self, validated_data):
        profile_data = self._extract_profile_data(validated_data)
        password = validated_data.pop("password")
        is_enabled = validated_data.pop("is_enabled", True)
        role = profile_data.pop("role")

        user = User(
            **validated_data,
            is_active=is_enabled,
            is_staff=role == UserProfile.ROLE_ADMIN,
        )
        user.set_password(password)
        user.save()

        profile = ensure_user_profile(user)
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.role = role
        profile.save()
        return user

    def update(self, instance, validated_data):
        profile_data = self._extract_profile_data(validated_data)
        password = validated_data.pop("password", None)
        is_enabled = validated_data.pop("is_enabled", instance.is_active)
        role = profile_data.pop("role")

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.is_active = is_enabled
        instance.is_staff = role == UserProfile.ROLE_ADMIN
        if password:
            instance.set_password(password)
        instance.save()

        profile = ensure_user_profile(instance)
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.role = role
        profile.save()
        return instance

    def _extract_profile_data(self, validated_data):
        return {
            "role": validated_data.pop("role"),
            "real_name": validated_data.pop("real_name", ""),
            "student_no": normalize_optional_value(validated_data.pop("student_no", "")),
            "teacher_no": normalize_optional_value(validated_data.pop("teacher_no", "")),
            "phone": validated_data.pop("phone", ""),
            "department": validated_data.pop("department", ""),
        }


class SelfProfileUpdateSerializer(serializers.ModelSerializer):
    real_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    department = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = User
        fields = [
            "email",
            "real_name",
            "phone",
            "department",
        ]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
        }

    def update(self, instance, validated_data):
        profile = ensure_user_profile(instance)
        instance.email = validated_data.get("email", instance.email)
        instance.save(update_fields=["email"])

        profile.real_name = validated_data.get("real_name", profile.real_name)
        profile.phone = validated_data.get("phone", profile.phone)
        profile.department = validated_data.get("department", profile.department)
        profile.save(update_fields=["real_name", "phone", "department", "updated_at"])
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        allow_blank=False,
        error_messages={"blank": "当前密码不能为空"},
    )
    new_password = serializers.CharField(
        write_only=True,
        allow_blank=False,
        min_length=6,
        error_messages={
            "blank": "新密码不能为空",
            "min_length": "新密码长度不能少于 6 位",
        },
    )
    confirm_password = serializers.CharField(
        write_only=True,
        allow_blank=False,
        error_messages={"blank": "确认密码不能为空"},
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "当前密码不正确"})

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的新密码不一致"})

        validate_password(attrs["new_password"], user=user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "用户名或密码错误",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        profile = ensure_user_profile(user)
        token["role"] = profile.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        ensure_user_profile(self.user)
        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
            "user": UserSerializer(self.user).data,
        }


class RefreshTokenResponseSerializer(TokenRefreshSerializer):
    default_error_messages = {
        "no_active_account": "当前令牌对应的账号不可用",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        return {"access_token": data["access"]}
