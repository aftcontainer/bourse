# mainapp/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

from .middleware import get_current_request
from .models import (
    JournalAudit, Client, Operation, Portefeuille, Role,
    Compte, Titre, Etablissement,
)

TRACKED_MODELS = [Client, Operation, Portefeuille, Role, Compte, Titre, Etablissement]


def _get_request_meta():
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    ip = request.META.get('REMOTE_ADDR') if request else None
    ua = request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''
    return (user if user and user.is_authenticated else None), ip, ua


def log_save(sender, instance, created, **kwargs):
    user, ip, ua = _get_request_meta()
    JournalAudit.objects.create(
        user=user,
        action='CREATE' if created else 'UPDATE',
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=ip,
        user_agent=ua,
    )


def log_delete(sender, instance, **kwargs):
    user, ip, ua = _get_request_meta()
    JournalAudit.objects.create(
        user=user,
        action='DELETE',
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=ip,
        user_agent=ua,
    )


for model in TRACKED_MODELS:
    post_save.connect(log_save, sender=model)
    post_delete.connect(log_delete, sender=model)

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    JournalAudit.objects.create(
        user=user, action='LOGIN',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    JournalAudit.objects.create(
        user=user, action='LOGOUT',
        ip_address=request.META.get('REMOTE_ADDR'),
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    JournalAudit.objects.create(
        action='LOGIN_FAILED',
        object_repr=credentials.get('username', 'inconnu'),
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
    )