from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import Profile


def get_role(user):
    """사용자의 역할을 반환합니다. 프로필이 없으면 None을 반환합니다."""

    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return None


def is_mentor(user):
    return get_role(user) == Profile.Role.MENTOR


def is_mentee(user):
    return get_role(user) == Profile.Role.MENTEE


def mentor_required(view_func):
    """멘토 역할만 접근할 수 있는 뷰에 사용하는 데코레이터입니다."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_mentor(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def mentee_required(view_func):
    """멘티(학생) 역할만 접근할 수 있는 뷰에 사용하는 데코레이터입니다."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_mentee(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
