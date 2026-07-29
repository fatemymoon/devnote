"""역할(멘토/멘티) 기반 접근 제어 도구 모음.

뷰 함수 위에 @mentor_required / @mentee_required를 붙여서
해당 역할이 아닌 사용자의 접근을 차단합니다.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied  # 403 Forbidden 에러

from .models import Profile


def get_role(user):
    """사용자의 역할을 반환합니다. 프로필이 없으면 None을 반환합니다."""

    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return None


def is_mentor(user):
    """이 사용자가 멘토인지 확인합니다."""
    return get_role(user) == Profile.Role.MENTOR


def is_mentee(user):
    """이 사용자가 멘티(학생)인지 확인합니다."""
    return get_role(user) == Profile.Role.MENTEE


def mentor_required(view_func):
    """멘토 역할만 접근할 수 있는 뷰에 사용하는 데코레이터입니다.

    원래 뷰 함수를 wrapper로 감싸서, 뷰 실행 전에 역할을 먼저 검사합니다.
    멘토가 아니면 403 에러를 발생시키고 뷰는 실행되지 않습니다.
    """

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
