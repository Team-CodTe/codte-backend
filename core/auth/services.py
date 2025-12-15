import requests
from core.models import Provider, User

GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GITHUB_USER_INFO_URL = "https://api.github.com/user"
GITHUB_EMAIL_INFO_URL = "https://api.github.com/user/emails"


class SocialLoginService:
    """소셜 로그인 관련 비즈니스 로직 서비스"""

    def __init__(self, user_model=None):
        """
        서비스에서 사용할 User 모델을 주입합니다.

        Args:
            user_model: User 모델 클래스 (기본값: core.models.User)
        """
        self.user_model = user_model or User

    def fetch_user_info(self, provider: str, access_token: str) -> dict:
        """
        소셜 로그인 provider에 따라 사용자 정보를 조회합니다.

        Args:
            provider: 소셜 로그인 제공자 (Provider.GITHUB / Provider.GOOGLE)
            access_token: OAuth access token (str)

        Returns:
            dict: {"email": str | None, "profile_img_url": str | None}

        Raises:
            ValueError: 유효하지 않은 provider 이거나, 계정 정보를 가져오지 못한 경우
        """
        # provider에 따라 사용자 정보 조회
        if provider == Provider.GITHUB:
            return self._fetch_github_user(access_token)
        if provider == Provider.GOOGLE:
            return self._fetch_google_user(access_token)
        raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

    def login_or_create_user(self, provider: str, user_data: dict):
        """
        사용자 정보를 기반으로 로그인 또는 회원가입을 처리합니다.

        Args:
            provider: 소셜 로그인 제공자 (Provider.GITHUB / Provider.GOOGLE)
            user_data: fetch_user_info에서 반환된 사용자 정보 (dict)

        Returns:
            tuple: (user, is_registration_required) - User 인스턴스와 추가 회원가입 필요 여부

        Raises:
            ValueError: 이메일이 없거나, 다른 provider로 이미 가입된 경우
        """
        # 사용자 데이터에서 필요한 필드 추출
        email = user_data.get("email")
        profile_img_url = user_data.get("profile_img_url")

        # 이메일 유효성 검사
        if not email:
            raise ValueError("계정 정보를 찾을 수 없습니다.")

        # 사용자 조회/생성
        user, user_created = self.user_model.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "provider": provider,
                "profile_img_url": profile_img_url,
            },
        )

        # provider 불일치 검사
        if user.provider != provider:
            raise ValueError(
                "이미 {}계정으로 가입된 이메일입니다.".format(user.provider)
            )

        # 프로필 이미지 동기화 (변경된 경우에만 업데이트)
        if (
            not user_created
            and profile_img_url
            and user.profile_img_url != profile_img_url
        ):
            user.profile_img_url = profile_img_url
            user.save(update_fields=["profile_img_url"])

        # 추가 정보 입력(백준 아이디 등)이 필요한지 판단
        is_registration_required = user_created or (user.boj_username is None)

        return user, is_registration_required

    def _fetch_google_user(self, access_token: str) -> dict:
        """
        Google access token으로 사용자 정보를 조회합니다.

        Args:
            access_token: OAuth access token (str)

        Returns:
            dict: {"email": str | None, "profile_img_url": str | None}

        Raises:
            ValueError: Google 계정 정보를 가져오지 못했거나, 유효하지 않은 계정인 경우
        """
        # Google userinfo API 호출
        try:
            response = requests.get(
                GOOGLE_USER_INFO_URL,
                params={"access_token": access_token},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("Google 계정 정보를 가져오는 중 오류가 발생했습니다.")

        # 응답 검증
        if not response.ok:
            raise ValueError("유효하지 않은 Google 계정입니다.")

        user_info = response.json()

        # 필요한 필드만 반환
        return {
            "email": user_info.get("email"),
            "profile_img_url": user_info.get("picture"),
        }

    def _fetch_github_user(self, access_token: str) -> dict:
        """
        GitHub access token으로 사용자 정보를 조회합니다.

        Args:
            access_token: OAuth access token (str)

        Returns:
            dict: {"email": str | None, "profile_img_url": str | None}

        Raises:
            ValueError: GitHub 계정 정보를 가져오지 못했거나, 유효하지 않은 계정인 경우
        """
        # GitHub user API 호출을 위한 Authorization 헤더 구성
        headers = {"Authorization": f"Bearer {access_token}"}

        # GitHub user API 호출
        try:
            response = requests.get(
                GITHUB_USER_INFO_URL,
                headers=headers,
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("GitHub 계정 정보를 가져오는 중 오류가 발생했습니다.")

        # 응답 검증
        if not response.ok:
            raise ValueError("유효하지 않은 GitHub 계정입니다.")

        user_data = response.json()
        email = user_data.get("email")

        # public email이 없는 경우 primary & verified 이메일 조회
        if not email:
            email = self._fetch_primary_github_email(headers)

        # 필요한 필드만 반환
        return {
            "email": email,
            "profile_img_url": user_data.get("avatar_url"),
        }

    def _fetch_primary_github_email(self, headers: dict) -> str | None:
        """
        GitHub 이메일 API에서 primary & verified 이메일을 조회합니다.

        Args:
            headers: GitHub API 요청 헤더 (Authorization 포함)

        Returns:
            str | None: primary & verified 이메일. 없으면 None.

        Raises:
            ValueError: GitHub 이메일 정보를 가져오는 중 네트워크 오류가 발생한 경우
        """
        # GitHub email API 호출
        try:
            email_response = requests.get(
                GITHUB_EMAIL_INFO_URL,
                headers=headers,
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("GitHub 이메일 정보를 가져오는 중 오류가 발생했습니다.")

        # 응답 검증
        if not email_response.ok:
            return None

        emails = email_response.json()

        # primary & verified 이메일 탐색
        for item in emails:
            if item.get("primary") and item.get("verified"):
                return item.get("email")

        return None
