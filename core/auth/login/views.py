from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class SocialLoginView(APIView):
    def post(self, request):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")

        user_data = None

        try:
            if provider == "github":
                user_data = self.validate_github(access_token)
            elif provider == "google":
                user_data = self.validate_google(access_token)
            else:
                return Response(
                    {"error": "유효하지 않은 소셜 로그인 제공자입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = user_data.get("email")
        profile_img_url = user_data.get("profile_img_url")

        if not email:
            return Response(
                {"error": "계정 정보를 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = User.objects.filter(email=email).first()

        if existing_user and existing_user.provider != provider:
            return Response(
                {
                    "error": "이미 {}계정으로 가입된 이메일입니다.".format(
                        existing_user.provider
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                if existing_user:
                    user = existing_user
                    created = False

                # 기존 유저의 경우에 프로필 이미지 업데이트(프로필 이미지가 변경될 수 있으므로)
                if profile_img_url:
                    user.profile_img_url = profile_img_url
                    user.save()
                else:
                    user = User.objects.create(
                        username=email,  # 우선 username을 email로 고정하고, 회원가입할 때 username을 다시 입력받게 함
                        email=email,
                        provider=provider,
                        profile_img_url=profile_img_url,
                    )
                    created = True
        except IntegrityError:
            return Response(
                {"error": "로그인 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # JWT 생성
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                "message": "로그인에 성공했습니다.",
                "user": {
                    "id": user.id,
                    "provider": user.provider,
                    "email": user.email,
                    "username": user.username,
                    "boj_username": user.boj_username,
                    "profile_img_url": user.profile_img_url,
                },
                "requires_registration": created,
            },
            status=status.HTTP_200_OK,
        )

        cookie_kwargs = {
            "httponly": True,
            "samesite": "Lax",
            "secure": False,  # 배포 시 True로 변경 필요(https 옵션)
        }

        response.set_cookie("access_token", access_token, **cookie_kwargs)
        response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)

        return response

    def validate_google(self, access_token):
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

        try:
            response = requests.get(
                user_info_url, params={"access_token": access_token}
            )
        except requests.exceptions.RequestException as e:
            raise ValueError("Google 계정 정보를 가져오는 중 오류가 발생했습니다.")

        if not response.ok:
            raise ValueError("유효하지 않은 Google 계정입니다.")

        user_info = response.json()

        return {
            "email": user_info.get("email"),
            "profile_img_url": user_info.get("picture"),
        }

    def validate_github(self, access_token):
        user_url = "https://api.github.com/user"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(user_url, headers=headers)
        except requests.exceptions.RequestException as e:
            raise ValueError("GitHub 계정 정보를 가져오는 중 오류가 발생했습니다.")

        if not response.ok:
            raise ValueError("유효하지 않은 GitHub 계정입니다.")

        user_data = response.json()
        email = user_data.get("email")

        if not email:
            email_url = "https://api.github.com/user/emails"

            try:
                email_response = requests.get(email_url, headers=headers)
            except requests.exceptions.RequestException as e:
                raise ValueError(
                    "GitHub 이메일 정보를 가져오는 중 오류가 발생했습니다."
                )

            if email_response.ok:
                emails = email_response.json()

                for e in emails:
                    if e["primary"] and e["verified"]:
                        email = e["email"]
                        break

        return {
            "email": email,
            "profile_img_url": user_data.get("avatar_url"),
        }
