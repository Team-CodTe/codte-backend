import requests
from django.db import IntegrityError, transaction

from core.models import Provider, User

GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GITHUB_USER_INFO_URL = "https://api.github.com/user"
GITHUB_EMAIL_INFO_URL = "https://api.github.com/user/emails"


class SocialLoginService:
    def __init__(self, user_model=None):
        self.user_model = user_model or User

    def fetch_user_info(self, provider: str, access_token: str) -> dict:
        if provider == Provider.GITHUB:
            return self._fetch_github_user(access_token)
        if provider == Provider.GOOGLE:
            return self._fetch_google_user(access_token)
        raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

    def login_or_create_user(self, provider: str, user_data: dict):
        email = user_data.get("email")
        profile_img_url = user_data.get("profile_img_url")

        if not email:
            raise ValueError("계정 정보를 찾을 수 없습니다.")

        existing_user = self.user_model.objects.filter(email=email).first()

        if existing_user and existing_user.provider != provider:
            raise ValueError(
                "이미 {}계정으로 가입된 이메일입니다.".format(existing_user.provider)
            )

        try:
            with transaction.atomic():
                if existing_user:
                    user = existing_user
                    created = False

                    if profile_img_url:
                        user.profile_img_url = profile_img_url
                        user.save(update_fields=["profile_img_url"])
                else:
                    user = self.user_model.objects.create(
                        username=email,
                        email=email,
                        provider=provider,
                        profile_img_url=profile_img_url,
                    )
                    created = True
        except IntegrityError:
            raise

        return user, created

    def _fetch_google_user(self, access_token: str) -> dict:
        try:
            response = requests.get(
                GOOGLE_USER_INFO_URL,
                params={"access_token": access_token},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("Google 계정 정보를 가져오는 중 오류가 발생했습니다.")

        if not response.ok:
            raise ValueError("유효하지 않은 Google 계정입니다.")

        user_info = response.json()

        return {
            "email": user_info.get("email"),
            "profile_img_url": user_info.get("picture"),
        }

    def _fetch_github_user(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                GITHUB_USER_INFO_URL,
                headers=headers,
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("GitHub 계정 정보를 가져오는 중 오류가 발생했습니다.")

        if not response.ok:
            raise ValueError("유효하지 않은 GitHub 계정입니다.")

        user_data = response.json()
        email = user_data.get("email")

        if not email:
            email = self._fetch_primary_github_email(headers)

        return {
            "email": email,
            "profile_img_url": user_data.get("avatar_url"),
        }

    def _fetch_primary_github_email(self, headers: dict) -> str | None:
        try:
            email_response = requests.get(
                GITHUB_EMAIL_INFO_URL,
                headers=headers,
                timeout=5,
            )
        except requests.exceptions.RequestException:
            raise ValueError("GitHub 이메일 정보를 가져오는 중 오류가 발생했습니다.")

        if not email_response.ok:
            return None

        emails = email_response.json()

        for item in emails:
            if item.get("primary") and item.get("verified"):
                return item.get("email")

        return None
