
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

app = FastAPI(
    title="CampusMate Notice API",
    description="CampusMate MVP용 충남대 실시간 공지 추천 API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CNU_BASE = "https://plus.cnu.ac.kr"
CNU_NOTICE_URL = "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0702&menu_dvs_cd=0702&site_dvs_cd=kr"
CNU_CALENDAR_URL = "https://plus.cnu.ac.kr/_prog/academic_calendar/?menu_dvs_cd=05020101&site_dvs_cd=kr"

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
        "persona_message": "야 이거 너한테 꽤 중요할 것 같은데. 컴공 3학년이면 졸업요건 변경은 한번 봐야 함.",
        "source_type": "sample"
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
        "persona_message": "수강신청 일정 떴다. 이번엔 장바구니부터 좀 챙겨라 ㅋㅋ",
        "source_type": "sample"
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
        "persona_message": "너 백엔드 관심 있다고 했잖아. 이 특강은 한번 들어봐도 될 듯.",
        "source_type": "sample"
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
        "persona_message": "아 맞다. 너 장학금 관심 있었지? 신청 기간 놓치면 아까우니까 확인해봐.",
        "source_type": "sample"
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
        "persona_message": "3학년이면 인턴도 슬슬 봐야지. 이거 백엔드 준비하는 사람한테 괜찮을 수도 있음.",
        "source_type": "sample"
    }
]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 CampusMateNoticeBot/3.0"}
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    raw = response.content

    candidates = [
        response.encoding,
        response.apparent_encoding,
        "utf-8",
        "euc-kr",
        "cp949",
    ]

    best_text = ""
    best_score = -999999

    for enc in candidates:
        if not enc:
            continue
        try:
            text = raw.decode(enc, errors="replace")
            korean_count = len(re.findall(r"[가-힣]", text))
            broken_count = text.count("�") + text.count("□")
            score = korean_count - broken_count * 20
            if score > best_score:
                best_score = score
                best_text = text
        except Exception:
            pass

    return best_text or response.text


def infer_category(title: str) -> str:
    if any(k in title for k in ["수강", "수업", "정정", "폐강", "증원"]):
        return "수강신청"
    if any(k in title for k in ["졸업", "학위", "논문", "수료"]):
        return "졸업요건"
    if "장학" in title:
        return "장학금"
    if any(k in title for k in ["취업", "인턴", "현장실습", "특강", "채용", "기업"]):
        return "진로"
    if any(k in title for k in ["휴학", "복학", "등록", "성적", "시험", "학적"]):
        return "학사"
    return "학사정보"


def infer_importance(category: str) -> str:
    return "high" if category in ["졸업요건", "수강신청", "장학금"] else "medium"


def infer_tags(title: str, category: str) -> List[str]:
    tags = ["cnu", "academic"]
    if category == "수강신청":
        tags += ["course", "registration", "schedule"]
    elif category == "졸업요건":
        tags += ["graduation", "requirement"]
    elif category == "장학금":
        tags += ["scholarship", "money"]
    elif category == "진로":
        tags += ["career", "job"]

    if any(k in title for k in ["컴퓨터", "SW", "소프트웨어", "개발", "코딩", "AI", "인공지능"]):
        tags += ["computer", "backend", "software"]
    if any(k in title for k in ["경영", "마케팅", "창업"]):
        tags += ["business", "marketing"]
    if any(k in title for k in ["간호", "병원", "실습"]):
        tags += ["nursing", "practice"]

    return list(dict.fromkeys(tags))


def make_persona_message(title: str, category: str) -> str:
    if category == "수강신청":
        return f"야 이거 수강 관련 공지인데 한번 봐라. '{title}'"
    if category == "졸업요건":
        return f"이건 좀 봐야겠다. 졸업 관련 공지 같음. '{title}'"
    if category == "장학금":
        return f"장학금 쪽 공지 올라왔더라. 놓치면 아까우니까 확인해봐. '{title}'"
    if category == "진로":
        return f"이건 진로 쪽으로 도움 될 수도 있겠다. '{title}'"
    return f"이 공지 한번 확인해봐. '{title}'"


def is_notice_title(text: str) -> bool:
    if not text or len(text) < 6 or len(text) > 150:
        return False

    skip = [
        "로그인", "사이트맵", "개인정보", "이메일", "충남대학교", "바로가기",
        "검색", "닫기", "목록", "처음", "이전", "다음", "마지막", "페이지",
        "첨부파일", "다운로드", "메뉴", "본문", "ENGLISH"
    ]
    if any(s in text for s in skip):
        return False

    keywords = [
        "202", "학기", "안내", "모집", "신청", "수강", "졸업", "장학",
        "등록", "휴학", "복학", "성적", "시험", "특강", "현장실습", "채용",
        "학사", "교육", "프로그램", "계절"
    ]
    return any(k in text for k in keywords)


def scrape_cnu_notices(limit: int = 10) -> List[Dict[str, Any]]:
    html = fetch_html(CNU_NOTICE_URL)
    soup = BeautifulSoup(html, "html.parser")
    notices = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = normalize_space(a.get_text(" "))
        href = a.get("href", "")

        if not is_notice_title(title) or title in seen:
            continue

        seen.add(title)
        category = infer_category(title)
        full_url = urljoin(CNU_BASE, href)

        notices.append({
            "id": 1000 + len(notices) + 1,
            "title": title,
            "category": category,
            "department": "all",
            "target_grade": "all",
            "importance": infer_importance(category),
            "summary": title,
            "tags": infer_tags(title, category),
            "source_url": full_url,
            "persona_message": make_persona_message(title, category),
            "source_type": "live_cnu_academic_notice"
        })

        if len(notices) >= limit:
            break

    return notices


def scrape_cnu_calendar(limit: int = 20) -> List[Dict[str, Any]]:
    html = fetch_html(CNU_CALENDAR_URL)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")
    lines = [normalize_space(line) for line in text.split("\n")]
    lines = [line for line in lines if line]

    items = []
    seen = set()
    keywords = ["수강신청", "개강", "종강", "등록금", "등록", "휴학", "복학", "성적", "졸업", "시험"]

    for line in lines:
        if not any(k in line for k in keywords):
            continue
        if line in seen or len(line) < 5 or len(line) > 140:
            continue

        seen.add(line)
        category = infer_category(line)

        items.append({
            "id": 2000 + len(items) + 1,
            "title": line,
            "category": category,
            "department": "all",
            "target_grade": "all",
            "importance": infer_importance(category),
            "summary": line,
            "tags": infer_tags(line, category) + ["calendar"],
            "source_url": CNU_CALENDAR_URL,
            "persona_message": make_persona_message(line, category),
            "source_type": "live_cnu_calendar"
        })

        if len(items) >= limit:
            break

    return items


def get_live_data() -> List[Dict[str, Any]]:
    data = []
    try:
        data += scrape_cnu_notices(limit=15)
    except Exception:
        pass
    try:
        data += scrape_cnu_calendar(limit=15)
    except Exception:
        pass
    return data


def score_notice(notice: Dict[str, Any], department: str, grade: Optional[int], interest: Optional[str]) -> int:
    score = 0

    if str(notice.get("source_type", "")).startswith("live_cnu"):
        score += 25

    if notice.get("department") == department:
        score += 40
    elif notice.get("department") == "all":
        score += 20

    if grade:
        target = notice.get("target_grade", "all")
        if target == "all" or str(grade) in str(target).split(","):
            score += 20

    if interest:
        interest_lower = interest.lower()
        title = notice.get("title", "")
        summary = notice.get("summary", "")
        tags = [tag.lower() for tag in notice.get("tags", [])]

        if interest_lower in tags:
            score += 30
        if interest_lower in title.lower() or interest_lower in summary.lower():
            score += 25

        interest_map = {
            "backend": ["백엔드", "개발", "소프트웨어", "SW", "코딩"],
            "scholarship": ["장학"],
            "graduation": ["졸업", "학위", "수료"],
            "course": ["수강", "정정", "폐강", "증원"],
            "internship": ["인턴", "현장실습", "채용"],
            "marketing": ["마케팅", "공모전"],
        }
        for keyword in interest_map.get(interest_lower, []):
            if keyword in title or keyword in summary:
                score += 20
                break

    if notice.get("importance") == "high":
        score += 20
    elif notice.get("importance") == "medium":
        score += 10

    return score


def make_reason(notice: Dict[str, Any], department: str, grade: Optional[int], interest: Optional[str]) -> str:
    reasons = []
    if str(notice.get("source_type", "")).startswith("live_cnu"):
        reasons.append("충남대 공개 데이터 기반")
    if notice.get("department") == department:
        reasons.append("사용자 학과와 관련 있음")
    elif notice.get("department") == "all":
        reasons.append("전체 학생 대상 공지")
    if grade and (notice.get("target_grade") == "all" or str(grade) in str(notice.get("target_grade", "")).split(",")):
        reasons.append(f"{grade}학년 대상")
    if interest:
        reasons.append(f"관심사({interest}) 기준 추천")
    if notice.get("importance") == "high":
        reasons.append("중요도 높음")
    return ", ".join(reasons) if reasons else "기본 추천"


@app.get("/")
def root():
    return {
        "message": "CampusMate Notice API is running",
        "version": "3.0.0",
        "endpoints": ["/notices", "/live-notices", "/calendar", "/recommendations"]
    }


@app.get("/live-notices")
def live_notices(limit: int = Query(10)):
    try:
        notices = scrape_cnu_notices(limit=limit)
        return {"source": CNU_NOTICE_URL, "count": len(notices), "notices": notices}
    except Exception as e:
        return {"source": CNU_NOTICE_URL, "count": 0, "error": str(e), "notices": []}


@app.get("/calendar")
def calendar(limit: int = Query(20)):
    try:
        items = scrape_cnu_calendar(limit=limit)
        return {"source": CNU_CALENDAR_URL, "count": len(items), "calendar": items}
    except Exception as e:
        return {"source": CNU_CALENDAR_URL, "count": 0, "error": str(e), "calendar": []}


@app.get("/notices")
def notices(
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    live: bool = Query(True),
    include_sample: bool = Query(True)
):
    results = []
    if live:
        results += get_live_data()
    if include_sample:
        results += SAMPLE_NOTICES

    if department:
        results = [n for n in results if n.get("department") == department or n.get("department") == "all"]
    if category:
        results = [n for n in results if n.get("category") == category]

    return {"count": len(results), "live": live, "include_sample": include_sample, "notices": results}


@app.get("/recommendations")
def recommendations(
    department: str = Query(...),
    grade: Optional[int] = Query(None),
    interest: Optional[str] = Query(None),
    limit: int = Query(5),
    live: bool = Query(True),
    include_sample: bool = Query(True),
    live_only: bool = Query(False)
):
    if live_only:
        data = get_live_data()
    else:
        data = []
        if live:
            data += get_live_data()
        if include_sample:
            data += SAMPLE_NOTICES

    scored = []
    for notice in data:
        score = score_notice(notice, department, grade, interest)
        if score > 0:
            scored.append({
                **notice,
                "recommendation_score": score,
                "recommendation_reason": make_reason(notice, department, grade, interest)
            })

    scored.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return {
        "user_context": {"department": department, "grade": grade, "interest": interest},
        "live": live,
        "include_sample": include_sample,
        "live_only": live_only,
        "count": min(len(scored), limit),
        "recommendations": scored[:limit]
    }
