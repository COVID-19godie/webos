from django.utils.dateparse import parse_datetime
from .models import Membership

def get_current_membership(request):
    if not request.user or not request.user.is_authenticated:
        return None

    tenant_id = (
        request.headers.get('X-Tenant-Id') or
        request.query_params.get('tenant_id') or
        request.data.get('tenant_id')
    )

    if tenant_id:
        membership = Membership.objects.select_related('tenant').filter(
            user=request.user,
            tenant_id=tenant_id
        ).first()
        if membership:
            return membership

    membership = Membership.objects.select_related('tenant').filter(
        user=request.user,
        is_default=True
    ).first()

    if not membership:
        membership = Membership.objects.select_related('tenant').filter(
            user=request.user
        ).first()

    return membership

def get_current_tenant(request):
    membership = get_current_membership(request)
    return membership.tenant if membership else None

def parse_client_datetime(value):
    if not value:
        return None
    if isinstance(value, str):
        return parse_datetime(value)
    return value
