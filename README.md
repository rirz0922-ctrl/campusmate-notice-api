# CampusMate Notice API

CampusMate MVP용 학교 공지 추천 API입니다.

## 1. 로컬 실행

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

실행 후 접속:

```text
http://127.0.0.1:8000
```

## 2. 주요 엔드포인트

### 전체 공지

```text
GET /notices
```

예시:

```text
http://127.0.0.1:8000/notices
```

### 맞춤 추천

```text
GET /recommendations?department=computer&grade=3&interest=backend
```

예시:

```text
http://127.0.0.1:8000/recommendations?department=computer&grade=3&interest=backend
```

## 3. 교내 AI 외부 API 등록

배포 후 Base URL에는 배포 주소를 입력합니다.

예:

```text
https://campusmate-notice-api.onrender.com
```

## 4. 현재 MVP 방식

현재는 실제 충남대 공지 크롤링이 아니라 샘플 공지 데이터를 사용합니다.

이후 실제 구현에서는 충남대 학사공지, 학과공지, 비교과 프로그램 데이터를 수집하여 NOTICES 데이터를 자동 갱신하는 방식으로 확장합니다.
