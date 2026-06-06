# CampusMate Notice API v3

CampusMate MVP용 충남대 실시간 공지 추천 API입니다.

## 실행

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Render Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 엔드포인트

```text
/
```

```text
/live-notices
```

```text
/calendar
```

```text
/notices?live=true&include_sample=true
```

```text
/recommendations?department=computer&grade=3&interest=backend
```

```text
/recommendations?department=computer&grade=3&interest=course&live_only=true
```

## v3 개선

- 한글 인코딩 깨짐 보정
- 충남대 공개 데이터 기본 가산점
- live_only 옵션 추가
- 샘플 데이터와 실시간 데이터 분리 테스트 가능
