from rest_framework.permissions import BasePermission

from .utils import ensure_user_profile


class RolePermission(BasePermission):
    allowed_roles = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        profile = ensure_user_profile(user)
        return profile.role in self.allowed_roles


class IsAdmin(RolePermission):
    allowed_roles = {"admin"}


class IsTeacher(RolePermission):
    allowed_roles = {"teacher"}


class IsStudent(RolePermission):
    allowed_roles = {"student"}
