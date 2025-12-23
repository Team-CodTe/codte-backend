from django.conf import settings

ACCESS_TOKEN_LIFETIME = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
REFRESH_TOKEN_LIFETIME = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]


def _get_secure_cookie_kwargs(max_age):
    """
    보안 쿠키 설정을 반환하는 헬퍼 함수

    Args:
        max_age: 쿠키 만료 시간 (초 단위)

    Returns:
        dict: 쿠키 설정 딕셔너리
    """
    kwargs = {
        "httponly": True,
        "samesite": "Lax",
        "secure": not settings.DEBUG,
        "max_age": max_age,
    }

    return kwargs


def set_secure_cookie(response, key, value, max_age):
    """
    응답에 보안 쿠키를 설정하는 헬퍼 함수

    Args:
        response: Django Response 객체
        key: 쿠키 키
        value: 쿠키 값
        max_age: 쿠키 만료 시간 (초 단위)
    """
    response.set_cookie(key, value, **_get_secure_cookie_kwargs(max_age))
