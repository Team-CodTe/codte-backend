from django.conf import settings

ACCESS_TOKEN_LIFETIME = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
REFRESH_TOKEN_LIFETIME = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

# Cookie names
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
IS_REGISTERED_COOKIE = "is_registered"


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
        "samesite": "None",  # 크로스 도메인 쿠키 전송 허용
        "secure": True,  # SameSite=None 사용 시 Secure 필수
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


def delete_auth_cookies(response):
    """
    인증 관련 쿠키를 삭제하는 헬퍼 함수

    Args:
        response: Django Response 객체
    """
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    response.delete_cookie(REFRESH_TOKEN_COOKIE)
    response.delete_cookie(IS_REGISTERED_COOKIE)
