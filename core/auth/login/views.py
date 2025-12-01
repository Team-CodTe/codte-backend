from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class SocialLoginView(APIView):
    def post(self, request, provider):
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
                    "error": "이미 {}로 가입된 이메일입니다.".format(
                        existing_user.provider
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            username=email, # 우선 username을 email로 고정하고, 회원가입할 때 username을 다시 입력받게 함
            defaults={
                "email": email,
                "provider": provider,
                "profile_img_url": profile_img_url,
            },
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response_data = {
            "message": "로그인에 성공했습니다.",
            "user": {
                "id": user.id,
                "provider": user.provider,
                "username": user.username,
                "email": user.email,
                "profile_img_url": user.profile_img_url,
            },
            "requires_registration": created,
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            samesite="Lax",
            secure=False,  # 배포 시 True로 변경 필요
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            samesite="Lax",
            secure=False,  # 배포 시 True로 변경 필요
        )

        return response

    def validate_google(self, access_token):
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(user_info_url, params={"access_token": access_token})

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
        response = requests.get(user_url, headers=headers)

        if not response.ok:
            raise ValueError("유효하지 않은 GitHub 계정입니다.")

        user_data = response.json()
        email = user_data.get("email")

        if not email:
            email_url = "https://api.github.com/user/emails"
            email_response = requests.get(email_url, headers=headers)

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
