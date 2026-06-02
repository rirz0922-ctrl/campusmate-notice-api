# CampusMate Notice API v2

CampusMate MVP용 충남대 공지 추천 API입니다.

## 로컬 실행

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## 주요 엔드포인트

### 기본 확인

```text
GET /
```

### 샘플 + live 공지

```text
GET /notices?live=true
```

### 충남대 학사정보 게시판 크롤링

```text
GET /live-notices
```

### 충남대 학사일정 크롤링

```text
GET /calendar
```

### 맞춤 추천

```text
GET /recommendations?department=computer&grade=3&interest=backend
```

## Render Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 주의

v2는 충남대 공개 페이지를 실시간으로 요청합니다.
학교 페이지 구조가 바뀌면 파싱 결과가 달라질 수 있습니다.
실제 서비스에서는 주기적 수집 + DB 저장 방식으로 개선하는 것이 좋습니다.
