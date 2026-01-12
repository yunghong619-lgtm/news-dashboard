"""
뉴스 대시보드 설정 파일
"""
import os

# 기본 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'news.db')

# Flask 설정
FLASK_HOST = '0.0.0.0'
FLASK_PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ============================================================
# 네이버 API 설정
# ============================================================
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', 'BYweSDPPg_dTZROwTX3b')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', 'RflXvc3Od7')

# 네이버 뉴스 검색 API
NAVER_SEARCH_API_URL = 'https://openapi.naver.com/v1/search/news.json'

# 네이버 뉴스 RSS 피드 URL
NAVER_RSS_FEEDS = {
    'IT': 'https://rss.news.naver.com/rss/news/category/105.xml',      # IT/과학
    '경제': 'https://rss.news.naver.com/rss/news/category/101.xml',    # 경제
    '사회': 'https://rss.news.naver.com/rss/news/category/102.xml',    # 사회
    '생활': 'https://rss.news.naver.com/rss/news/category/103.xml',    # 생활/문화
    '정치': 'https://rss.news.naver.com/rss/news/category/100.xml',    # 정치
    '세계': 'https://rss.news.naver.com/rss/news/category/104.xml',    # 세계
}

# 검색할 키워드 (네이버 검색 API용)
SEARCH_KEYWORDS = {
    'IT': ['AI', '인공지능', '반도체', '스타트업', '빅데이터', '클라우드'],
    '경제': ['주식', '부동산', '금리', '환율', '코스피'],
    '사회': ['교육', '의료', '안전', '환경'],
    '생활': ['건강', '여행', '문화', '맛집'],
}

# 카테고리
CATEGORIES = ['IT', '경제', '사회', '생활', '정치', '세계']

# 뉴스 출처 (참고용)
SOURCES = ['네이버뉴스']

# 수집 설정
NEWS_PER_CATEGORY = 20  # 카테고리당 수집할 뉴스 수
SEARCH_DISPLAY_COUNT = 10  # 검색 API 결과 수
