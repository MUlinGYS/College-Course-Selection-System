def ensure_user_profile(user):
    from users.models import UserProfile

    default_role = UserProfile.ROLE_ADMIN if user.is_superuser else UserProfile.ROLE_STUDENT
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": default_role})

    if user.is_superuser and profile.role != UserProfile.ROLE_ADMIN:
        profile.role = UserProfile.ROLE_ADMIN
        profile.save(update_fields=["role", "updated_at"])

    return profile
