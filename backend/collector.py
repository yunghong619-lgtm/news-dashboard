"""
뉴스 수집기 - Google News RSS 사용 (해외 서버 호환)
"""
import requests
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from collections import Counter
from email.utils import parsedate_to_datetime
import urllib.parse

from database import insert_news, insert_keywords, clear_all_data, init_database, get_all_news


def clean_html(text):
    """HTML 태그 및 특수문자 제거"""
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-zA-Z]+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_rss_date(date_str):
    """RSS 날짜 문자열 파싱"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ============================================================
# Google News RSS 수집 (해외 서버에서도 작동)
# ============================================================

# 카테고리별 검색어
CATEGORY_QUERIES = {
    'IT': ['AI 인공지능', '반도체', '스타트업', '테크'],
    '경제': ['주식 코스피', '부동산', '금리 환율'],
    '사회': ['사회 이슈', '교육 정책'],
    '생활': ['건강 생활', '여행 문화'],
}

def fetch_google_news(query, category):
    """
    Google News RSS에서 뉴스 수집
    """
    news_list = []

    try:
        # Google News RSS URL (한국어)
        encoded_query = urllib.parse.quote(query)
        url = f'https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        for item in items[:10]:  # 검색어당 10개
            title_el = item.find('title')
            link_el = item.find('link')
            pub_date_el = item.find('pubDate')
            source_el = item.find('source')

            title = clean_html(title_el.text if title_el is not None else '')
            source = source_el.text if source_el is not None else 'Google News'

            news = {
                'title': title,
                'description': f'{query} 관련 뉴스',
                'content': title,
                'source': source,
                'category': category,
                'url': link_el.text if link_el is not None else '',
                'image_url': '',
                'published_at': parse_rss_date(pub_date_el.text if pub_date_el is not None else '')
            }

            news_list.append(news)

        print(f"[Google] {category}/{query}: {len(news_list)}개")

    except Exception as e:
        print(f"[Google 오류] {category}/{query}: {e}")

    return news_list


def collect_from_google_news():
    """Google News에서 카테고리별 뉴스 수집"""
    all_news = []

    for category, queries in CATEGORY_QUERIES.items():
        for query in queries:
            news_list = fetch_google_news(query, category)
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
    Google News에서 뉴스 수집 및 저장
    """
    print("=" * 50)
    print("Google News 수집 시작")
    print("=" * 50)

    all_news = []

    # Google News에서 수집
    print("\n[1] Google News 수집 중...")
    google_news = collect_from_google_news()
    all_news.extend(google_news)

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
