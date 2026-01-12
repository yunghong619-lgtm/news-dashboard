"""
SQLite 데이터베이스 관리
"""
import sqlite3
import os
from config import DB_PATH, DATA_DIR


def get_connection():
    """데이터베이스 연결 반환"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = get_connection()
    cursor = conn.cursor()

    # 뉴스 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            source TEXT,
            category TEXT,
            url TEXT,
            image_url TEXT,
            published_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 키워드 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            date DATE,
            UNIQUE(keyword, date)
        )
    ''')

    conn.commit()
    conn.close()
    print("데이터베이스 초기화 완료")


def insert_news(news_list):
    """뉴스 데이터 삽입"""
    conn = get_connection()
    cursor = conn.cursor()

    for news in news_list:
        cursor.execute('''
            INSERT INTO news (title, description, content, source, category, url, image_url, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            news.get('title'),
            news.get('description'),
            news.get('content'),
            news.get('source'),
            news.get('category'),
            news.get('url'),
            news.get('image_url'),
            news.get('published_at')
        ))

    conn.commit()
    conn.close()


def insert_keywords(keywords_dict, date):
    """키워드 데이터 삽입 또는 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()

    for keyword, count in keywords_dict.items():
        cursor.execute('''
            INSERT INTO keywords (keyword, count, date)
            VALUES (?, ?, ?)
            ON CONFLICT(keyword, date) DO UPDATE SET count = count + ?
        ''', (keyword, count, date, count))

    conn.commit()
    conn.close()


def get_all_news(limit=100):
    """모든 뉴스 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM news
        ORDER BY published_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_news_by_category(category):
    """카테고리별 뉴스 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM news
        WHERE category = ?
        ORDER BY published_at DESC
    ''', (category,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_source_stats():
    """출처별 뉴스 통계"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT source, COUNT(*) as count
        FROM news
        GROUP BY source
        ORDER BY count DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_category_stats():
    """카테고리별 뉴스 통계"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM news
        GROUP BY category
        ORDER BY count DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_keyword_trends(limit=20):
    """키워드 트렌드 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT keyword, SUM(count) as total_count
        FROM keywords
        GROUP BY keyword
        ORDER BY total_count DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def clear_all_data():
    """모든 데이터 삭제 (테스트용)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM news')
    cursor.execute('DELETE FROM keywords')

    conn.commit()
    conn.close()
    print("모든 데이터 삭제 완료")
