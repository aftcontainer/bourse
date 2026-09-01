from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                Q(email__iexact=username) | Q(username__iexact=username)
            ).order_by("id").first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

class RoleBackend(BaseBackend):
    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        role_ids = user_obj.userrole_set.filter(
            role__is_active=True
        ).values_list('role_id', flat=True)

        perms = Permission.objects.filter(
            roles__id__in=role_ids
        ).values_list('content_type__app_label', 'codename')

        return {f"{app_label}.{codename}" for app_label, codename in perms}

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)