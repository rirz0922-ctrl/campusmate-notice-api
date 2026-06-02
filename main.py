from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI(
    title="CampusMate Notice API",
    description="CampusMate MVP용 학교 공지 추천 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Notice(BaseModel):
    id: int
    title: str
    category: str
    department: str
    target_grade: str
    importance: str
    summary: str
    tags: List[str]
    source_url: str
    persona_message: str

NOTICES = [
    {
        "id": 1,
        "title": "컴퓨터공학과 졸업요건 변경 안내",
        "category": "졸업요건",
        "department": "computer",
        "target_grade": "3,4",
        "importance": "high",
        "summary": "전공선택 인정 기준과 캡스톤디자인 이수 조건 일부 변경",
        "tags": ["computer", "graduation", "course", "grade3"],
        "source_url": "https://plus.cnu.ac.kr",
        "persona_message": "야 이거 너한테 꽤 중요할 것 같은데. 컴공 3학년이면 졸업요건 변경은 한번 봐야 함."
    },
    {
        "id": 2,
        "title": "2026학년도 1학기 수강신청 일정 안내",
        "category": "수강신청",
        "department": "all",
        "target_grade": "all",
        "importance": "high",
        "summary": "수강신청, 정정기간, 폐강 기준 안내",
        "tags": ["course", "registration", "schedule"],
        "source_url": "https://plus.cnu.ac.kr",
        "persona_message": "수강신청 일정 떴다. 이번엔 장바구니부터 좀 챙겨라 ㅋㅋ"
    },
    {
        "id": 3,
        "title": "백엔드 개발자 커리어 특강",
        "category": "진로",
        "department": "computer",
        "target_grade": "2,3,4",
        "importance": "medium",
        "summary": "현직 백엔드 개발자의 커리어 로드맵 및 포트폴리오 특강",
        "tags": ["computer", "backend", "career", "lecture"],
        "source_url": "https://with.cnu.ac.kr",
        "persona_message": "너 백엔드 관심 있다고 했잖아. 이 특강은 한번 들어봐도 될 듯."
    },
    {
        "id": 4,
        "title": "교내 장학금 신청 안내",
        "category": "장학금",
        "department": "all",
        "target_grade": "all",
        "importance": "high",
        "summary": "성적우수 및 가계곤란 장학금 신청 기간과 제출 서류 안내",
        "tags": ["scholarship", "money", "application"],
        "source_url": "https://plus.cnu.ac.kr",
        "persona_message": "아 맞다. 너 장학금 관심 있었지? 신청 기간 놓치면 아까우니까 확인해봐."
    },
    {
        "id": 5,
        "title": "IT 기업 현장실습 및 인턴십 모집",
        "category": "진로",
        "department": "computer",
        "target_grade": "3,4",
        "importance": "medium",
        "summary": "IT 기업 연계 현장실습 및 인턴십 프로그램 모집",
        "tags": ["computer", "internship", "career", "backend"],
        "source_url": "https://with.cnu.ac.kr",
        "persona_message": "3학년이면 인턴도 슬슬 봐야지. 이거 백엔드 준비하는 사람한테 괜찮을 수도 있음."
    },
    {
        "id": 6,
        "title": "간호학과 임상실습 일정 안내",
        "category": "실습",
        "department": "nursing",
        "target_grade": "3,4",
        "importance": "high",
        "summary": "간호학과 임상실습 일정 및 사전교육 안내",
        "tags": ["nursing", "practice", "hospital"],
        "source_url": "https://plus.cnu.ac.kr",
        "persona_message": "실습 일정 올라왔더라. 간호 3학년이면 이건 꼭 확인해야 할 듯."
    },
    {
        "id": 7,
        "title": "경영학과 마케팅 공모전 안내",
        "category": "공모전",
        "department": "business",
        "target_grade": "all",
        "importance": "medium",
        "summary": "마케팅 전략 기획 공모전 참가자 모집",
        "tags": ["business", "marketing", "contest"],
        "source_url": "https://with.cnu.ac.kr",
        "persona_message": "마케팅 쪽 관심 있으면 이 공모전 괜찮아 보이는데?"
    }
]

def score_notice(notice: dict, department: str, grade: Optional[int], interest: Optional[str]) -> int:
    score = 0

    if notice["department"] == department:
        score += 40
    elif notice["department"] == "all":
        score += 20

    if grade:
        target = notice["target_grade"]
        if target == "all" or str(grade) in target.split(","):
            score += 20

    if interest:
        interest_lower = interest.lower()
        if interest_lower in [tag.lower() for tag in notice["tags"]]:
            score += 30
        if interest_lower in notice["summary"].lower() or interest_lower in notice["title"].lower():
            score += 20

    if notice["importance"] == "high":
        score += 20
    elif notice["importance"] == "medium":
        score += 10

    return score

def make_reason(notice: dict, department: str, grade: Optional[int], interest: Optional[str]) -> str:
    reasons = []

    if notice["department"] == department:
        reasons.append("사용자 학과와 관련 있음")
    elif notice["department"] == "all":
        reasons.append("전체 학생 대상 공지")

    if grade and (notice["target_grade"] == "all" or str(grade) in notice["target_grade"].split(",")):
        reasons.append(f"{grade}학년 대상")

    if interest and interest.lower() in [tag.lower() for tag in notice["tags"]]:
        reasons.append(f"관심사({interest})와 관련 있음")

    if notice["importance"] == "high":
        reasons.append("중요도 높음")

    return ", ".join(reasons) if reasons else "기본 추천"

@app.get("/")
def root():
    return {
        "message": "CampusMate Notice API is running",
        "endpoints": ["/notices", "/recommendations"]
    }

@app.get("/notices")
def get_notices(
    department: Optional[str] = Query(None, description="computer, business, nursing, all"),
    category: Optional[str] = Query(None, description="졸업요건, 수강신청, 장학금, 진로 등")
):
    results = NOTICES

    if department:
        results = [n for n in results if n["department"] == department or n["department"] == "all"]

    if category:
        results = [n for n in results if n["category"] == category]

    return {
        "count": len(results),
        "notices": results
    }

@app.get("/recommendations")
def get_recommendations(
    department: str = Query(..., description="예: computer, business, nursing"),
    grade: Optional[int] = Query(None, description="예: 3"),
    interest: Optional[str] = Query(None, description="예: backend, scholarship, marketing"),
    limit: int = Query(3, description="추천 개수")
):
    scored = []
    for notice in NOTICES:
        score = score_notice(notice, department, grade, interest)
        if score > 0:
            scored.append({
                **notice,
                "recommendation_score": score,
                "recommendation_reason": make_reason(notice, department, grade, interest)
            })

    scored.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return {
        "user_context": {
            "department": department,
            "grade": grade,
            "interest": interest
        },
        "count": min(len(scored), limit),
        "recommendations": scored[:limit]
    }
