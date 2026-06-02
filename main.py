from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI(
    title="CampusMate Notice API",
    description="CampusMate MVP용 충남대 공지 추천 API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CNU_ACADEMIC_NOTICE_URL = "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0702&menu_dvs_cd=0702&site_dvs_cd=kr"
CNU_ACADEMIC_CALENDAR_URL = "https://plus.cnu.ac.kr/_prog/academic_calendar/?menu_dvs_cd=05020101&site_dvs_cd=kr"

SAMPLE_NOTICES = [
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
    }
]

def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def infer_category(title: str) -> str:
    t = title.lower()
    if "수강" in title or "course" in t:
        return "수강신청"
    if "졸업" in title or "학위" in title:
        return "졸업요건"
    if "장학" in title:
        return "장학금"
    if "취업" in title or "인턴" in title or "현장실습" in title or "특강" in title:
        return "진로"
    if "휴학" in title or "복학" in title:
        return "학사"
    return "학사정보"

def infer_tags(title: str, category: str) -> List[str]:
    tags = ["cnu", "academic"]
    mapping = {
        "수강신청": ["course", "registration"],
        "졸업요건": ["graduation"],
        "장학금": ["scholarship"],
        "진로": ["career"],
        "학사": ["academic"],
    }
    tags.extend(mapping.get(category, []))
    if "백엔드" in title or "개발" in title or "SW" in title or "소프트웨어" in title:
        tags.extend(["computer", "backend"])
    return list(dict.fromkeys(tags))

def make_persona_message(title: str, category: str) -> str:
    if category == "수강신청":
        return f"야 이거 수강 관련 공지인데 한번 봐라. 제목은 '{title}'임."
    if category == "졸업요건":
        return f"이건 좀 봐야겠다. 졸업 관련 공지 같음. '{title}'"
    if category == "장학금":
        return f"장학금 쪽 공지 올라왔더라. 놓치면 아까우니까 확인해봐. '{title}'"
    if category == "진로":
        return f"진로 쪽으로 도움 될 수도 있겠다. '{title}'"
    return f"이 공지 한번 확인해봐. '{title}'"

def scrape_cnu_academic_notices(limit: int = 10) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 CampusMateNoticeBot/1.0"
    }
    response = requests.get(CNU_ACADEMIC_NOTICE_URL, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = normalize_space(a.get_text(" "))
        if not text or len(text) < 4:
            continue
        if ("mode=V" in href or "no=" in href) and text not in seen:
            seen.add(text)
            if href.startswith("/"):
                url = "https://plus.cnu.ac.kr" + href
            elif href.startswith("http"):
                url = href
            else:
                url = "https://plus.cnu.ac.kr/_prog/_board/" + href

            category = infer_category(text)
            candidates.append({
                "id": 1000 + len(candidates) + 1,
                "title": text,
                "category": category,
                "department": "all",
                "target_grade": "all",
                "importance": "high" if category in ["수강신청", "졸업요건", "장학금"] else "medium",
                "summary": text,
                "tags": infer_tags(text, category),
                "source_url": url,
                "persona_message": make_persona_message(text, category),
                "source_type": "live_cnu_academic_notice"
            })

        if len(candidates) >= limit:
            break

    return candidates

def scrape_cnu_calendar(limit: int = 20) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 CampusMateNoticeBot/1.0"
    }
    response = requests.get(CNU_ACADEMIC_CALENDAR_URL, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n")
    lines = [normalize_space(line) for line in text.split("\n")]
    lines = [line for line in lines if line]

    items = []
    pattern = re.compile(r"(\d{2}\.\d{2}|\d{2}\.\d{2}\(.+?\).*?~.*?\d{2}\.\d{2}|\d{2}\.\d{2}.*?~.*?\d{2}\.\d{2})")

    for line in lines:
        if any(keyword in line for keyword in ["수강신청", "개강", "종강", "등록금", "휴학", "복학", "성적", "졸업"]):
            if len(line) > 5 and line not in [item["title"] for item in items]:
                category = infer_category(line)
                items.append({
                    "id": 2000 + len(items) + 1,
                    "title": line,
                    "category": category,
                    "department": "all",
                    "target_grade": "all",
                    "importance": "high" if category in ["수강신청", "졸업요건"] else "medium",
                    "summary": line,
                    "tags": infer_tags(line, category) + ["calendar"],
                    "source_url": CNU_ACADEMIC_CALENDAR_URL,
                    "persona_message": make_persona_message(line, category),
                    "source_type": "live_cnu_calendar"
                })
        if len(items) >= limit:
            break

    return items

def get_all_notices(use_live: bool = False) -> List[Dict[str, Any]]:
    notices = list(SAMPLE_NOTICES)
    if use_live:
        try:
            notices = scrape_cnu_academic_notices(limit=10) + scrape_cnu_calendar(limit=10) + notices
        except Exception as e:
            # Render나 학교 사이트 상황에 따라 크롤링 실패할 수 있으므로 샘플 데이터로 fallback
            notices = list(SAMPLE_NOTICES)
    return notices

def score_notice(notice: dict, department: str, grade: Optional[int], interest: Optional[str]) -> int:
    score = 0

    if notice.get("department") == department:
        score += 40
    elif notice.get("department") == "all":
        score += 20

    if grade:
        target = notice.get("target_grade", "all")
        if target == "all" or str(grade) in target.split(","):
            score += 20

    if interest:
        interest_lower = interest.lower()
        tags = [tag.lower() for tag in notice.get("tags", [])]
        if interest_lower in tags:
            score += 30
        if interest_lower in notice.get("summary", "").lower() or interest_lower in notice.get("title", "").lower():
            score += 20

    if notice.get("importance") == "high":
        score += 20
    elif notice.get("importance") == "medium":
        score += 10

    return score

def make_reason(notice: dict, department: str, grade: Optional[int], interest: Optional[str]) -> str:
    reasons = []

    if notice.get("department") == department:
        reasons.append("사용자 학과와 관련 있음")
    elif notice.get("department") == "all":
        reasons.append("전체 학생 대상 공지")

    if grade and (notice.get("target_grade") == "all" or str(grade) in notice.get("target_grade", "").split(",")):
        reasons.append(f"{grade}학년 대상")

    if interest and interest.lower() in [tag.lower() for tag in notice.get("tags", [])]:
        reasons.append(f"관심사({interest})와 관련 있음")

    if notice.get("importance") == "high":
        reasons.append("중요도 높음")

    if notice.get("source_type"):
        reasons.append("충남대 공개 데이터 기반")

    return ", ".join(reasons) if reasons else "기본 추천"

@app.get("/")
def root():
    return {
        "message": "CampusMate Notice API is running",
        "version": "2.0.0",
        "endpoints": ["/notices", "/recommendations", "/live-notices", "/calendar"]
    }

@app.get("/notices")
def get_notices(
    department: Optional[str] = Query(None, description="computer, business, nursing, all"),
    category: Optional[str] = Query(None, description="졸업요건, 수강신청, 장학금, 진로 등"),
    live: bool = Query(False, description="충남대 공개 데이터 포함 여부")
):
    results = get_all_notices(use_live=live)

    if department:
        results = [n for n in results if n.get("department") == department or n.get("department") == "all"]

    if category:
        results = [n for n in results if n.get("category") == category]

    return {
        "count": len(results),
        "live": live,
        "notices": results
    }

@app.get("/live-notices")
def get_live_notices(limit: int = Query(10, description="가져올 공지 개수")):
    try:
        notices = scrape_cnu_academic_notices(limit=limit)
        return {
            "source": CNU_ACADEMIC_NOTICE_URL,
            "count": len(notices),
            "notices": notices
        }
    except Exception as e:
        return {
            "source": CNU_ACADEMIC_NOTICE_URL,
            "count": 0,
            "error": str(e),
            "notices": []
        }

@app.get("/calendar")
def get_calendar(limit: int = Query(20, description="가져올 학사일정 개수")):
    try:
        items = scrape_cnu_calendar(limit=limit)
        return {
            "source": CNU_ACADEMIC_CALENDAR_URL,
            "count": len(items),
            "calendar": items
        }
    except Exception as e:
        return {
            "source": CNU_ACADEMIC_CALENDAR_URL,
            "count": 0,
            "error": str(e),
            "calendar": []
        }

@app.get("/recommendations")
def get_recommendations(
    department: str = Query(..., description="예: computer, business, nursing"),
    grade: Optional[int] = Query(None, description="예: 3"),
    interest: Optional[str] = Query(None, description="예: backend, scholarship, marketing"),
    limit: int = Query(3, description="추천 개수"),
    live: bool = Query(True, description="충남대 공개 데이터 포함 여부")
):
    notices = get_all_notices(use_live=live)
    scored = []

    for notice in notices:
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
        "live": live,
        "count": min(len(scored), limit),
        "recommendations": scored[:limit]
    }
