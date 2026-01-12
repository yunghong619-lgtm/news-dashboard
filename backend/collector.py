"""
뉴스 수집기 - 네이버 뉴스 RSS 및 검색 API 연동
"""
import requests
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from collections import Counter
from email.utils import parsedate_to_datetime

from config import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_SEARCH_API_URL,
    NAVER_RSS_FEEDS, SEARCH_KEYWORDS, CATEGORIES,
    NEWS_PER_CATEGORY, SEARCH_DISPLAY_COUNT
)
from database import insert_news, insert_keywords, clear_all_data, init_database, get_all_news


def clean_html(text):
    """HTML 태그 및 특수문자 제거"""
    if not text:
        return ''
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수 문자 정리
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_rss_date(date_str):
    """RSS 날짜 문자열 파싱"""
    try:
        # RFC 2822 형식 파싱
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ============================================================
# 네이버 뉴스 RSS 수집
# ============================================================

def fetch_naver_rss(category, url):
    """
    네이버 뉴스 RSS 피드에서 뉴스 수집

    Args:
        category: 카테고리명
        url: RSS 피드 URL

    Returns:
        list: 뉴스 목록
    """
    news_list = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # XML 파싱
        root = ET.fromstring(response.content)

        # RSS 아이템 추출
        items = root.findall('.//item')

        for item in items[:NEWS_PER_CATEGORY]:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')

            # 출처 추출 (title에서)
            title_text = clean_html(title.text if title is not None else '')
            source = '네이버뉴스'

            # 언론사 추출 시도
            if ' - ' in title_text:
                parts = title_text.rsplit(' - ', 1)
                if len(parts) == 2:
                    source = parts[1].strip()

            news = {
                'title': title_text,
                'description': clean_html(description.text if description is not None else ''),
                'content': clean_html(description.text if description is not None else ''),
                'source': source,
                'category': category,
                'url': link.text if link is not None else '',
                'image_url': '',
                'published_at': parse_rss_date(pub_date.text if pub_date is not None else '')
            }

            news_list.append(news)

        print(f"[RSS] {category}: {len(news_list)}개 수집")

    except Exception as e:
        print(f"[RSS 오류] {category}: {e}")

    return news_list


def collect_from_rss():
    """모든 카테고리의 RSS 피드에서 뉴스 수집"""
    all_news = []

    for category, url in NAVER_RSS_FEEDS.items():
        news_list = fetch_naver_rss(category, url)
        all_news.extend(news_list)

    return all_news


# ============================================================
# 네이버 뉴스 검색 API
# ============================================================

def search_naver_news(query, display=SEARCH_DISPLAY_COUNT):
    """
    네이버 뉴스 검색 API로 뉴스 검색

    Args:
        query: 검색어
        display: 결과 개수 (최대 100)

    Returns:
        list: 뉴스 목록
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
            'sort': 'date'  # 최신순
        }

        response = requests.get(NAVER_SEARCH_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        for item in data.get('items', []):
            # 날짜 파싱
            pub_date = item.get('pubDate', '')

            news = {
                'title': clean_html(item.get('title', '')),
                'description': clean_html(item.get('description', '')),
                'content': clean_html(item.get('description', '')),
                'source': '네이버검색',
                'category': 'IT',  # 기본값, 나중에 설정
                'url': item.get('link', ''),
                'image_url': '',
                'published_at': parse_rss_date(pub_date)
            }

            news_list.append(news)

    except Exception as e:
        print(f"[검색 API 오류] {query}: {e}")

    return news_list


def collect_from_search_api():
    """키워드별로 네이버 검색 API에서 뉴스 수집"""
    all_news = []

    for category, keywords in SEARCH_KEYWORDS.items():
        for keyword in keywords[:2]:  # 카테고리당 2개 키워드만
            news_list = search_naver_news(keyword)

            # 카테고리 설정
            for news in news_list:
                news['category'] = category
                news['source'] = f'검색:{keyword}'

            all_news.extend(news_list)
            print(f"[검색] {category}/{keyword}: {len(news_list)}개 수집")

    return all_news


# ============================================================
# 키워드 추출
# ============================================================

# 주요 키워드 목록
KEYWORD_LIST = [
    # IT
    'AI', '인공지능', 'ChatGPT', '반도체', '삼성전자', 'SK하이닉스', '엔비디아',
    '스타트업', '빅데이터', '클라우드', '5G', '6G', '메타버스', '블록체인',
    '자율주행', '전기차', '테슬라', '애플', '구글', '마이크로소프트', 'OpenAI',

    # 경제
    '코스피', '코스닥', '주식', '부동산', '금리', '환율', '달러', '원화',
    '한국은행', '기준금리', '인플레이션', '물가', 'GDP', '수출', '무역',

    # 사회
    '국회', '대통령', '정부', '교육', '의료', '건강보험', '연금', '고용',
    '청년', '주거', '교통', '안전', '환경', '기후변화',

    # 생활
    '날씨', '여행', '맛집', '카페', '문화', '공연', '영화', '드라마',
    'K-POP', 'BTS', '스포츠', '축구', '야구'
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
    모든 소스에서 뉴스 수집 및 저장

    Returns:
        int: 수집된 뉴스 개수
    """
    print("=" * 50)
    print("네이버 뉴스 수집 시작")
    print("=" * 50)

    all_news = []

    # 1. RSS 피드에서 수집
    print("\n[1] RSS 피드 수집 중...")
    rss_news = collect_from_rss()
    all_news.extend(rss_news)

    # 2. 검색 API에서 수집
    print("\n[2] 검색 API 수집 중...")
    search_news = collect_from_search_api()
    all_news.extend(search_news)

    # 3. 중복 제거 (제목 기준)
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title = news.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(news)

    print(f"\n총 {len(unique_news)}개 뉴스 (중복 제거 후)")

    # 4. 기존 데이터 삭제 및 새 데이터 저장
    clear_all_data()
    insert_news(unique_news)

    # 5. 키워드 추출 및 저장
    keywords = extract_keywords_from_news(unique_news)
    today = datetime.now().strftime('%Y-%m-%d')
    insert_keywords(keywords, today)

    print(f"키워드 {len(keywords)}개 저장")
    print("=" * 50)

    return len(unique_news)


def collect_and_store_dummy_news():
    """
    하위 호환성을 위한 래퍼 함수
    실제로는 네이버 뉴스를 수집함
    """
    return collect_all_news()


# ============================================================
# 테스트
# ============================================================

if __name__ == '__main__':
    init_database()
    count = collect_all_news()
    print(f"\n수집 완료: {count}개 뉴스")
