"""
뉴스 수집기 - 네이버 검색 API 사용
"""
import requests
import re
import html
from datetime import datetime
from collections import Counter
from email.utils import parsedate_to_datetime
import urllib.parse

from database import insert_news, insert_keywords, clear_all_data, init_database, get_all_news
from config import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET,
    NAVER_SEARCH_API_URL, SEARCH_KEYWORDS, CATEGORIES
)


def clean_html(text):
    """HTML 태그 및 특수문자 제거"""
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_naver_date(date_str):
    """네이버 API 날짜 문자열 파싱"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ============================================================
# 네이버 검색 API 수집
# ============================================================

def fetch_naver_news(query, category, display=10):
    """
    네이버 검색 API에서 뉴스 수집
    """
    news_list = []

    try:
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }

        params = {
            'query': query,
            'display': display,
            'start': 1,
            'sort': 'date'  # 최신순 정렬
        }

        response = requests.get(
            NAVER_SEARCH_API_URL,
            headers=headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()

        data = response.json()
        items = data.get('items', [])

        for item in items:
            title = clean_html(item.get('title', ''))
            description = clean_html(item.get('description', ''))

            # 출처 추출 (originallink에서 도메인 추출)
            original_link = item.get('originallink', '')
            source = extract_source(original_link)

            news = {
                'title': title,
                'description': description,
                'content': description,
                'source': source,
                'category': category,
                'url': item.get('link', ''),
                'image_url': '',
                'published_at': parse_naver_date(item.get('pubDate', ''))
            }

            news_list.append(news)

        print(f"[네이버] {category}/{query}: {len(news_list)}개")

    except Exception as e:
        print(f"[네이버 오류] {category}/{query}: {e}")

    return news_list


def extract_source(url):
    """URL에서 출처(언론사) 추출"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        # 알려진 언론사 매핑
        source_map = {
            'chosun.com': '조선일보',
            'donga.com': '동아일보',
            'joongang.co.kr': '중앙일보',
            'hankyung.com': '한국경제',
            'mk.co.kr': '매일경제',
            'sedaily.com': '서울경제',
            'hani.co.kr': '한겨레',
            'khan.co.kr': '경향신문',
            'yna.co.kr': '연합뉴스',
            'yonhapnews.co.kr': '연합뉴스',
            'news1.kr': '뉴스1',
            'newsis.com': '뉴시스',
            'edaily.co.kr': '이데일리',
            'mt.co.kr': '머니투데이',
            'etnews.com': '전자신문',
            'zdnet.co.kr': 'ZDNet',
            'bloter.net': '블로터',
            'sbs.co.kr': 'SBS',
            'kbs.co.kr': 'KBS',
            'mbc.co.kr': 'MBC',
            'jtbc.co.kr': 'JTBC',
            'ytn.co.kr': 'YTN',
        }

        for key, name in source_map.items():
            if key in domain:
                return name

        # 매핑 없으면 도메인 반환
        return domain.replace('www.', '').split('.')[0]
    except:
        return '뉴스'


def collect_from_naver_api():
    """네이버 검색 API에서 카테고리별 뉴스 수집"""
    all_news = []

    for category, keywords in SEARCH_KEYWORDS.items():
        for keyword in keywords:
            news_list = fetch_naver_news(keyword, category, display=10)
            all_news.extend(news_list)

    return all_news


# ============================================================
# 키워드 추출
# ============================================================

KEYWORD_LIST = [
    'AI', '인공지능', 'ChatGPT', '반도체', '삼성전자', 'SK하이닉스', '엔비디아',
    '스타트업', '빅데이터', '클라우드', '5G', '메타버스', '블록체인',
    '자율주행', '전기차', '테슬라', '애플', '구글', '마이크로소프트',
    '코스피', '코스닥', '주식', '부동산', '금리', '환율', '달러',
    '한국은행', '인플레이션', '물가', 'GDP', '수출',
    '국회', '대통령', '정부', '교육', '의료', '건강보험',
    '날씨', '여행', '맛집', '문화', '공연', '영화', '드라마', 'K-POP'
]


def extract_keywords_from_news(news_list):
    """뉴스 목록에서 키워드 추출"""
    keyword_counter = Counter()

    for news in news_list:
        text = f"{news.get('title', '')} {news.get('description', '')}"

        for keyword in KEYWORD_LIST:
            if keyword.lower() in text.lower():
                keyword_counter[keyword] += 1

    return dict(keyword_counter)


# ============================================================
# 메인 수집 함수
# ============================================================

def collect_all_news():
    """
    네이버 검색 API에서 뉴스 수집 및 저장
    """
    print("=" * 50)
    print("네이버 뉴스 수집 시작")
    print("=" * 50)

    all_news = []

    # 네이버 검색 API에서 수집
    print("\n[1] 네이버 검색 API 수집 중...")
    naver_news = collect_from_naver_api()
    all_news.extend(naver_news)

    # 중복 제거
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title = news.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(news)

    print(f"\n총 {len(unique_news)}개 뉴스 (중복 제거 후)")

    # 저장
    clear_all_data()
    insert_news(unique_news)

    # 키워드 저장
    keywords = extract_keywords_from_news(unique_news)
    today = datetime.now().strftime('%Y-%m-%d')
    insert_keywords(keywords, today)

    print(f"키워드 {len(keywords)}개 저장")
    print("=" * 50)

    return len(unique_news)


def collect_and_store_dummy_news():
    """하위 호환성 래퍼"""
    return collect_all_news()


if __name__ == '__main__':
    init_database()
    count = collect_all_news()
    print(f"\n수집 완료: {count}개 뉴스")
