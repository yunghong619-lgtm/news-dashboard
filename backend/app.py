"""
Flask API 서버
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

from config import FLASK_HOST, FLASK_PORT, DEBUG, CATEGORIES
from database import (
    init_database, get_all_news, get_news_by_category,
    get_source_stats, get_category_stats, get_keyword_trends
)
from collector import collect_all_news
from stock import get_all_stock_data, get_watchlist_stocks, get_hot_stocks

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# ============================================================
# 앱 시작 시 초기화 (Gunicorn 호환)
# ============================================================
def initialize_app():
    """서버 시작 시 데이터베이스 초기화 및 뉴스 수집"""
    import traceback

    print("=" * 50)
    print("새솔's 뉴스피드 서버 시작!")
    print("=" * 50)

    try:
        # 데이터베이스 초기화
        print("[1] 데이터베이스 초기화 중...")
        init_database()
        print("[1] 데이터베이스 초기화 완료!")

        # 뉴스 수집 (매번 새로 수집 - Render 무료 플랜은 DB 초기화됨)
        print("[2] 네이버 뉴스 수집 중...")
        count = collect_all_news()
        print(f"[2] 뉴스 {count}개 수집 완료!")

    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        print(traceback.format_exc())

    print("=" * 50)
    print("서버 준비 완료!")
    print("=" * 50)

# 앱 로드 시 초기화 실행
initialize_app()


# ============================================================
# 정적 파일 서빙
# ============================================================

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """정적 파일 서빙"""
    return send_from_directory(app.static_folder, filename)


# ============================================================
# API 엔드포인트
# ============================================================

@app.route('/api/news', methods=['GET'])
def get_news():
    """
    뉴스 목록 조회

    Query Parameters:
        - category: 카테고리 필터 (선택)
        - limit: 최대 개수 (기본값: 100)
    """
    category = request.args.get('category')
    limit = request.args.get('limit', 100, type=int)

    if category and category in CATEGORIES:
        news = get_news_by_category(category)
    else:
        news = get_all_news(limit)

    return jsonify({
        'success': True,
        'count': len(news),
        'data': news
    })


@app.route('/api/trends', methods=['GET'])
def get_trends():
    """
    트렌드 데이터 조회
    - 출처별 통계
    - 카테고리별 통계
    - 키워드 트렌드
    """
    source_stats = get_source_stats()
    category_stats = get_category_stats()
    keyword_trends = get_keyword_trends(20)

    return jsonify({
        'success': True,
        'data': {
            'sources': source_stats,
            'categories': category_stats,
            'keywords': keyword_trends
        }
    })


@app.route('/api/stats/sources', methods=['GET'])
def get_sources():
    """출처별 통계"""
    stats = get_source_stats()
    return jsonify({
        'success': True,
        'data': stats
    })


@app.route('/api/stats/categories', methods=['GET'])
def get_categories():
    """카테고리별 통계"""
    stats = get_category_stats()
    return jsonify({
        'success': True,
        'data': stats
    })


@app.route('/api/stats/keywords', methods=['GET'])
def get_keywords():
    """키워드 트렌드"""
    limit = request.args.get('limit', 20, type=int)
    trends = get_keyword_trends(limit)
    return jsonify({
        'success': True,
        'data': trends
    })


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """뉴스 실시간 수집 (POST)"""
    import traceback
    try:
        count = collect_all_news()
        return jsonify({
            'success': True,
            'message': f'{count}개의 뉴스를 수집했습니다.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/collect', methods=['GET'])
def collect_data():
    """뉴스 수집 (GET) - GitHub Actions용"""
    import traceback
    from datetime import datetime
    try:
        count = collect_all_news()
        return jsonify({
            'success': True,
            'message': f'{count}개의 뉴스를 수집했습니다.',
            'count': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/debug', methods=['GET'])
def debug_info():
    """디버그 정보 확인"""
    import traceback
    from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_RSS_FEEDS

    result = {
        'api_configured': bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET),
        'client_id_length': len(NAVER_CLIENT_ID) if NAVER_CLIENT_ID else 0,
        'rss_feeds': list(NAVER_RSS_FEEDS.keys()),
        'news_count': len(get_all_news(100)),
        'test_results': {}
    }

    # RSS 테스트
    try:
        import requests
        test_url = NAVER_RSS_FEEDS.get('IT', '')
        resp = requests.get(test_url, timeout=5)
        result['test_results']['rss_status'] = resp.status_code
        result['test_results']['rss_length'] = len(resp.content)
    except Exception as e:
        result['test_results']['rss_error'] = str(e)

    # 검색 API 테스트
    try:
        import requests
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }
        resp = requests.get(
            'https://openapi.naver.com/v1/search/news.json',
            headers=headers,
            params={'query': 'AI', 'display': 1},
            timeout=5
        )
        result['test_results']['search_status'] = resp.status_code
        result['test_results']['search_response'] = resp.json() if resp.status_code == 200 else resp.text[:200]
    except Exception as e:
        result['test_results']['search_error'] = str(e)

    return jsonify(result)


@app.route('/api/categories', methods=['GET'])
def list_categories():
    """사용 가능한 카테고리 목록"""
    return jsonify({
        'success': True,
        'data': CATEGORIES
    })


# ============================================================
# 주식 API 엔드포인트
# ============================================================

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """전체 주식 데이터 조회"""
    import traceback
    try:
        data = get_all_stock_data()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/stocks/watchlist', methods=['GET'])
def get_watchlist():
    """관심 종목 (보유 종목) 조회"""
    import traceback
    try:
        data = get_watchlist_stocks()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/stocks/hot', methods=['GET'])
def get_hot():
    """인기 종목 조회"""
    import traceback
    try:
        data = get_hot_stocks()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================================
# 에러 핸들러
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not Found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal Server Error'
    }), 500


# ============================================================
# 메인
# ============================================================

if __name__ == '__main__':
    print(f"\n로컬 서버: http://localhost:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG)
