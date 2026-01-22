"""Gemini API를 사용한 코드 리뷰 서비스"""

from google import genai
from google.genai import types
from django.conf import settings


class GeminiService:
    """Gemini API를 사용한 코드 리뷰 서비스"""

    REVIEW_PROMPT = """
# Role
당신은 친절하고 예리한 '알고리즘 코딩 테스트 멘토'입니다.

# Input Context
사용자가 작성한 문제 풀이 글의 내용이 입력됩니다.
**주의:** 스터디마다 템플릿이 다르므로, 입력 형식이 일정하지 않습니다(접근 방법이나 회고가 없을 수도 있음).
- 텍스트에서 코드 로직과 의도를 유추하세요.
  - 코드가 없다면 작성되어있는 나머지 내용을 이용해서 코드 로직과 의도를 유추하세요.
- 코드가 포함되어 있다면 정합성과 효율성을 최우선으로 분석하세요.

# Review Guidelines
1. **핵심 위주:** 사소한 스타일(띄어쓰기 등)보다는 로직 오류, 시간 복잡도, 치명적인 비효율성에 집중하세요.
2. **조건부 피드백:** '회고'나 '접근 방법'이 없는 경우, 해당 내용에 대한 언급은 생략하고 코드 자체에 집중하세요.
3. **간결함:** 불필요한 미사여구를 줄이고, 핵심만 간결하게 전달하세요.

# Output Format
반드시 다음 마크다운 형식을 따르세요(존댓말 사용). 다만, 수학 수식 표현을 사용하지 마세요(예시: $O(n^2)$ -> O(n^2), $K$ -> K, $N$ -> N).

### 💡 핵심 요약
- (코드의 장점이나 전체적인 접근 방식에 대한 1줄 평)

### 🛠️ 개선이 필요한 점 (최대 3개, 없으면 생략)
- (중요도가 가장 높다고 생각되는 것부터 작성하고, 가능하면 각 점에 대해 2~3줄 정도로 간결하게 작성)

### 📊 복잡도
- **시간 복잡도:** O(...)
- **공간 복잡도:** O(...)

### 🍯 한 줄 팁
- (문제를 더 쉽게 풀 수 있는 키워드나 트릭 1개)
"""

    def __init__(self):
        """Gemini API 클라이언트 초기화"""
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        self.client = genai.Client(api_key=api_key)

    def generate_code_review(
        self, content: str, problem_number: int | None = None
    ) -> str:
        """
        풀이 내용에 대한 AI 코드 리뷰를 생성합니다.

        Args:
            content: 풀이 노트 내용 (Markdown, 형식이 불규칙할 수 있음)
            problem_number: 백준 문제 번호 (선택)

        Returns:
            str: AI가 생성한 코드 리뷰 (Markdown)
        """

        problem_info = f"백준 문제 번호: {problem_number}" if problem_number else ""
        prompt = (
            f"{self.REVIEW_PROMPT}\n"
            f"----------------------------------------\n"
            f"# 유저 입력 데이터\n{problem_info}\n\n{content}"
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                ),
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API 호출 중 오류가 발생했습니다: {str(e)}")
