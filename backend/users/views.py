from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin
from core.swagger import KEYWORD_PARAMETER, PAGINATION_PARAMETERS, ROLE_PARAMETER, paginated_response
from core.utils import ensure_user_profile
from .serializers import (
    AdminUserWriteSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RefreshTokenResponseSerializer,
    SelfProfileUpdateSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    @extend_schema(
        summary="用户登录",
        description="使用用户名和密码登录，返回访问令牌、刷新令牌和当前用户信息。",
        request=LoginSerializer,
        responses=inline_serializer(
            name="LoginResponse",
            fields={
                "access_token": serializers.CharField(),
                "refresh_token": serializers.CharField(),
                "user": UserSerializer(),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    serializer_class = RefreshTokenResponseSerializer

    @extend_schema(
        summary="刷新访问令牌",
        description="使用刷新令牌换取新的访问令牌。",
        request=inline_serializer(
            name="RefreshTokenRequest",
            fields={"refresh": serializers.CharField()},
        ),
        responses=inline_serializer(
            name="RefreshTokenResponseBody",
            fields={"access_token": serializers.CharField()},
        ),
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    @extend_schema(
        summary="退出登录",
        description="前端调用的退出登录接口，当前仅返回成功标记，由前端自行清理本地令牌。",
        request=None,
        responses=inline_serializer(
            name="LogoutResponse",
            fields={"ok": serializers.BooleanField()},
        ),
    )
    def post(self, request):
        return Response({"ok": True})


class MeView(APIView):
    serializer_class = UserSerializer

    @extend_schema(summary="获取当前用户信息", description="返回当前登录用户的基本信息和角色资料。", responses=UserSerializer)
    def get(self, request):
        ensure_user_profile(request.user)
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="更新当前用户资料",
        description="更新当前登录用户可自行维护的资料字段，如邮箱、姓名、电话和部门。",
        request=SelfProfileUpdateSerializer,
        responses=UserSerializer,
    )
    def put(self, request):
        ensure_user_profile(request.user)
        serializer = SelfProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class MePasswordView(APIView):
    @extend_schema(
        summary="修改当前用户密码",
        description="校验旧密码后更新当前登录用户密码。",
        request=ChangePasswordSerializer,
        responses=inline_serializer(
            name="ChangePasswordResponse",
            fields={
                "ok": serializers.BooleanField(),
                "message": serializers.CharField(),
            },
        ),
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "message": "密码修改成功，请重新登录"})


class UserListCreateView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def _serialize_users(self, queryset_or_page):
        users = list(queryset_or_page)
        for user in users:
            ensure_user_profile(user)
        return UserSerializer(users, many=True).data

    @extend_schema(
        operation_id="users_list",
        summary="获取用户列表",
        description="管理员查询系统用户。支持按角色和关键字筛选；传入 `paginate=1` 时，返回真实分页结构。",
        parameters=PAGINATION_PARAMETERS + [ROLE_PARAMETER, KEYWORD_PARAMETER],
        responses=paginated_response("PaginatedUserListResponse", UserSerializer),
    )
    def get(self, request):
        queryset = User.objects.select_related("profile").all().order_by("id")
        role = request.query_params.get("role")
        keyword = request.query_params.get("q")

        if role:
            queryset = queryset.filter(profile__role=role)

        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(profile__real_name__icontains=keyword)
                | Q(profile__student_no__icontains=keyword)
                | Q(profile__teacher_no__icontains=keyword)
                | Q(profile__department__icontains=keyword)
            )

        if should_paginate(request):
            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request, view=self)
            return paginator.get_paginated_response(self._serialize_users(page))

        return Response(self._serialize_users(queryset))

    @extend_schema(
        summary="创建用户",
        description="管理员创建学生、教师或管理员账号，并同步写入资料信息。",
        request=AdminUserWriteSerializer,
        responses=UserSerializer,
    )
    def post(self, request):
        serializer = AdminUserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def get_object(self, user_id):
        user = get_object_or_404(User, pk=user_id)
        ensure_user_profile(user)
        return user

    @extend_schema(operation_id="users_detail", summary="获取用户详情", description="管理员根据用户 ID 查看单个用户详情。", responses=UserSerializer)
    def get(self, request, user_id):
        user = self.get_object(user_id)
        return Response(UserSerializer(user).data)

    @extend_schema(
        summary="更新用户",
        description="管理员更新指定用户的账号信息、资料字段和启用状态。",
        request=AdminUserWriteSerializer,
        responses=UserSerializer,
    )
    def put(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserWriteSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)

    @extend_schema(summary="删除用户", description="管理员删除指定用户，但不能删除当前登录账号。", request=None, responses={204: None})
    def delete(self, request, user_id):
        user = self.get_object(user_id)
        if user == request.user:
            return Response(
                {"message": "不能删除当前登录用户"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
