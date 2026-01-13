"""
주식 정보 모듈 - Yahoo Finance 사용
"""
import yfinance as yf
from datetime import datetime, timedelta

# 관심 종목 (와이프 보유 종목)
WATCHLIST = {
    '한화오션': '042660.KS',
    '풍산': '103140.KS'
}

# 인기 종목 (코스피 대표 종목들)
HOT_STOCKS = {
    '삼성전자': '005930.KS',
    'SK하이닉스': '000660.KS',
    'LG에너지솔루션': '373220.KS',
    '현대차': '005380.KS',
    'NAVER': '035420.KS',
    '카카오': '035720.KS',
}


def get_stock_info(ticker_symbol):
    """
    개별 종목 정보 조회
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', 0)

        # 등락률 계산
        if previous_close and previous_close > 0:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
        else:
            change = 0
            change_percent = 0

        return {
            'symbol': ticker_symbol,
            'name': info.get('shortName', ticker_symbol),
            'currentPrice': current_price,
            'previousClose': previous_close,
            'change': round(change, 0),
            'changePercent': round(change_percent, 2),
            'dayHigh': info.get('dayHigh', 0),
            'dayLow': info.get('dayLow', 0),
            'volume': info.get('volume', 0),
            'marketCap': info.get('marketCap', 0),
        }
    except Exception as e:
        print(f"[Stock Error] {ticker_symbol}: {e}")
        return None


def get_stock_history(ticker_symbol, period='1mo'):
    """
    종목 히스토리 데이터 조회 (차트용)
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period)

        if hist.empty:
            return []

        data = []
        for date, row in hist.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 0),
                'high': round(row['High'], 0),
                'low': round(row['Low'], 0),
                'close': round(row['Close'], 0),
                'volume': int(row['Volume'])
            })

        return data
    except Exception as e:
        print(f"[Stock History Error] {ticker_symbol}: {e}")
        return []


def get_watchlist_stocks():
    """
    관심 종목 (와이프 보유) 정보 조회
    """
    result = []
    for name, ticker in WATCHLIST.items():
        info = get_stock_info(ticker)
        if info:
            info['displayName'] = name
            info['history'] = get_stock_history(ticker, '1mo')
            result.append(info)
    return result


def get_hot_stocks():
    """
    인기 종목 정보 조회
    """
    result = []
    for name, ticker in HOT_STOCKS.items():
        info = get_stock_info(ticker)
        if info:
            info['displayName'] = name
            result.append(info)

    # 등락률 기준 정렬
    result.sort(key=lambda x: abs(x.get('changePercent', 0)), reverse=True)
    return result


def get_all_stock_data():
    """
    전체 주식 데이터 조회 (프론트엔드용)
    """
    return {
        'watchlist': get_watchlist_stocks(),
        'hotStocks': get_hot_stocks(),
        'updatedAt': datetime.now().isoformat()
    }


if __name__ == '__main__':
    # 테스트
    print("=== 관심 종목 ===")
    for stock in get_watchlist_stocks():
        print(f"{stock['displayName']}: {stock['currentPrice']:,}원 ({stock['changePercent']:+.2f}%)")

    print("\n=== 인기 종목 ===")
    for stock in get_hot_stocks():
        print(f"{stock['displayName']}: {stock['currentPrice']:,}원 ({stock['changePercent']:+.2f}%)")
