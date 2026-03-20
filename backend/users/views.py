from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.pagination import StandardPagination, should_paginate
from core.permissions import IsAdmin
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


class RefreshView(TokenRefreshView):
    serializer_class = RefreshTokenResponseSerializer


class LogoutView(APIView):
    def post(self, request):
        return Response({"ok": True})


class MeView(APIView):
    def get(self, request):
        ensure_user_profile(request.user)
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        ensure_user_profile(request.user)
        serializer = SelfProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class MePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "message": "密码修改成功，请重新登录"})


class UserListCreateView(APIView):
    permission_classes = [IsAdmin]

    def _serialize_users(self, queryset_or_page):
        users = list(queryset_or_page)
        for user in users:
            ensure_user_profile(user)
        return UserSerializer(users, many=True).data

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

    def post(self, request):
        serializer = AdminUserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, user_id):
        user = get_object_or_404(User, pk=user_id)
        ensure_user_profile(user)
        return user

    def get(self, request, user_id):
        user = self.get_object(user_id)
        return Response(UserSerializer(user).data)

    def put(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserWriteSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)

    def delete(self, request, user_id):
        user = self.get_object(user_id)
        if user == request.user:
            return Response(
                {"message": "不能删除当前登录用户"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
