import random
from typing import List, Optional

import requests

SOLVED_AC_URL = "https://solved.ac/api/v3"


class SolvedAC:
    """solved.ac에서 문제를 추출하는 서비스"""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def build_search_query(
        self,
        tier_min: int,
        tier_max: int,
        min_solved: Optional[int] = None,
        max_solved: Optional[int] = None,
        exclude_usernames: Optional[List[str]] = None,
    ) -> str:
        """
        solved.ac 검색 쿼리 문자열 생성

        Args:
            tier_min: 최소 티어 (1=Bronze5, 30=Ruby1)
            tier_max: 최대 티어
            min_solved: 최소 푼 사람 수
            max_solved: 최대 푼 사람 수
            exclude_usernames: 제외할 사용자 닉네임 목록 (이미 푼 문제 제외)

        Returns:
            검색 쿼리 문자열
        """
        query_parts = []

        # 티어 범위 추가 (숫자로 전달)
        query_parts.append(f"*{tier_min}..{tier_max}")

        # 푼 사람 수 범위 추가
        if min_solved is not None or max_solved is not None:
            min_s = str(min_solved) if min_solved is not None else ""
            max_s = str(max_solved) if max_solved is not None else ""
            query_parts.append(f"s#{min_s}..{max_s}")

        # 유저들이 이미 푼 문제 제외
        if exclude_usernames:
            for username in exclude_usernames:
                if username and username.strip():
                    query_parts.append(f"-@{username.strip()}")

        # 제출 가능한 문제만
        query_parts.append("o?true")

        # 한국어 문제만
        query_parts.append("%ko")

        return " ".join(query_parts)

    def search_problems(self, query: str, count: int = 10) -> List[dict]:
        """
        solved.ac API로 문제 검색

        Args:
            query: 검색 쿼리 문자열
            count: 반환할 문제 개수

        Returns:
            문제 목록 (각 문제는 problemId, title, tier 포함)
        """
        response = requests.get(
            f"{SOLVED_AC_URL}/search/problem",
            params={
                "query": query,
                "sort": "random",
                "page": 1,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        problems = data.get("items", [])

        # 필요한 개수보다 많으면 랜덤 선택
        if len(problems) > count:
            problems = random.sample(problems, count)

        return problems[:count]

    def get_problem_by_id(self, problem_id: int) -> dict:
        """
        문제 ID로 문제 정보 조회

        Args:
            problem_id: 백준 문제 번호

        Returns:
            문제 정보 dict (problemId, titleKo, level 등)

        Raises:
            ProblemNotFoundError: 문제를 찾을 수 없는 경우
        """
        response = requests.get(
            f"{SOLVED_AC_URL}/problem/show",
            params={"problemId": problem_id},
            timeout=self.timeout,
        )

        if response.status_code == 404:
            raise ProblemNotFoundError(problem_id)

        response.raise_for_status()
        return response.json()


class ProblemNotFoundError(Exception):
    """문제를 찾을 수 없는 경우 발생하는 예외"""

    def __init__(self, problem_id: int):
        self.problem_id = problem_id
        super().__init__(f"{problem_id}번 문제를 찾을 수 없습니다.")
