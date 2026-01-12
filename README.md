# 뉴스 트렌드 대시보드

실시간 뉴스 동향을 시각화하는 웹 대시보드입니다.

## 기능

- 뉴스 목록 조회
- 카테고리별 필터링
- 출처별 통계 차트
- 키워드 트렌드 분석
- 더미 데이터 새로고침

## 프로젝트 구조

```
news-dashboard/
├── backend/
│   ├── app.py          # Flask 서버
│   ├── collector.py    # 뉴스 수집 (더미/NewsAPI)
│   ├── database.py     # SQLite 관리
│   └── config.py       # 설정
├── frontend/
│   ├── index.html      # 메인 페이지
│   ├── style.css       # 스타일
│   └── app.js          # Chart.js 대시보드
├── data/
│   └── news.db         # SQLite 데이터베이스
├── requirements.txt
└── README.md
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd news-dashboard
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
cd backend
python app.py
```

### 3. 브라우저에서 접속

```
http://localhost:5000
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/news` | 뉴스 목록 (category 파라미터로 필터링) |
| GET | `/api/trends` | 트렌드 데이터 (출처/카테고리/키워드) |
| GET | `/api/stats/sources` | 출처별 통계 |
| GET | `/api/stats/categories` | 카테고리별 통계 |
| GET | `/api/stats/keywords` | 키워드 트렌드 |
| POST | `/api/refresh` | 더미 데이터 새로고침 |
| GET | `/api/categories` | 카테고리 목록 |

## NewsAPI 연동 방법

현재는 더미 데이터로 동작합니다. 실제 뉴스 API를 연동하려면:

### 1. API 키 발급

[https://newsapi.org](https://newsapi.org) 에서 무료 API 키를 발급받으세요.

### 2. 환경변수 설정

**Windows:**
```cmd
set NEWSAPI_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export NEWSAPI_KEY=your-api-key-here
```

### 3. collector.py 수정

`collector.py`의 `fetch_from_newsapi()` 함수를 사용하여 실제 뉴스를 가져올 수 있습니다.

```python
from collector import fetch_from_newsapi

# 뉴스 가져오기
news_list = fetch_from_newsapi(query='한국', page_size=50)
```

## 카테고리

- 정치
- 경제
- 사회
- 기술
- 스포츠
- 연예
- 국제

## 기술 스택

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **API:** NewsAPI (선택사항)

## 라이선스

MIT License
