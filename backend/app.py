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

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# ============================================================
# 앱 시작 시 초기화 (Gunicorn 호환)
# ============================================================
def initialize_app():
    """서버 시작 시 데이터베이스 초기화 및 뉴스 수집"""
    print("=" * 50)
    print("새솔's 뉴스피드 서버 시작!")
    print("=" * 50)

    # 데이터베이스 초기화
    init_database()

    # 뉴스가 없으면 네이버에서 수집
    if len(get_all_news(1)) == 0:
        print("\n네이버 뉴스 수집 중...")
        collect_all_news()

    print("초기화 완료!")

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
    """네이버 뉴스 실시간 수집"""
    try:
        count = collect_all_news()
        return jsonify({
            'success': True,
            'message': f'네이버에서 {count}개의 뉴스를 수집했습니다.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/categories', methods=['GET'])
def list_categories():
    """사용 가능한 카테고리 목록"""
    return jsonify({
        'success': True,
        'data': CATEGORIES
    })


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
