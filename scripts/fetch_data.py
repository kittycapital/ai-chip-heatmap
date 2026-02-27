#!/usr/bin/env python3
"""
AI/반도체 밸류체인 트래커 - 데이터 수집
Yahoo Finance에서 종목 데이터 + 환율 수집, USD 기준 수익률 계산
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import pandas as pd

# ── 종목 정의 ──────────────────────────────────────────────
STOCKS = {
    # 설계 (Design)
    "NVDA":  {"name": "엔비디아",       "category": "설계", "color": "#76b900", "currency": "USD"},
    "AMD":   {"name": "AMD",           "category": "설계", "color": "#ed1c24", "currency": "USD"},
    "AVGO":  {"name": "브로드컴",       "category": "설계", "color": "#cc0000", "currency": "USD"},
    "QCOM":  {"name": "퀄컴",          "category": "설계", "color": "#3253dc", "currency": "USD"},
    "ARM":   {"name": "ARM홀딩스",      "category": "설계", "color": "#0091bd", "currency": "USD"},
    # 제조 (Foundry)
    "TSM":   {"name": "TSMC",          "category": "제조", "color": "#e30613", "currency": "USD"},
    "INTC":  {"name": "인텔",           "category": "제조", "color": "#0071c5", "currency": "USD"},
    "GFS":   {"name": "글로벌파운드리",   "category": "제조", "color": "#00a651", "currency": "USD"},
    # 장비 (Equipment)
    "ASML":  {"name": "ASML",          "category": "장비", "color": "#0f238c", "currency": "USD"},
    "AMAT":  {"name": "어플라이드",      "category": "장비", "color": "#f37021", "currency": "USD"},
    "LRCX":  {"name": "램리서치",        "category": "장비", "color": "#003da5", "currency": "USD"},
    "KLAC":  {"name": "KLA",           "category": "장비", "color": "#6d2077", "currency": "USD"},
    # 메모리 (Memory)
    "MU":         {"name": "마이크론",     "category": "메모리", "color": "#00b2e2", "currency": "USD"},
    "005930.KS":  {"name": "삼성전자",     "category": "메모리", "color": "#1428a0", "currency": "KRW"},
    "000660.KS":  {"name": "SK하이닉스",   "category": "메모리", "color": "#e4002b", "currency": "KRW"},
    # AI 인프라 (Infrastructure)
    "SMCI":  {"name": "슈퍼마이크로",     "category": "AI 인프라", "color": "#00539b", "currency": "USD"},
    "DELL":  {"name": "델 테크놀로지",    "category": "AI 인프라", "color": "#007db8", "currency": "USD"},
    "VRT":   {"name": "버티브홀딩스",     "category": "AI 인프라", "color": "#00843d", "currency": "USD"},
    "CRWV":  {"name": "코어위브",        "category": "AI 인프라", "color": "#ff6600", "currency": "USD"},
    # 클라우드 & AI (Cloud & AI)
    "MSFT":  {"name": "마이크로소프트",   "category": "클라우드 & AI", "color": "#00a4ef", "currency": "USD"},
    "GOOGL": {"name": "알파벳",          "category": "클라우드 & AI", "color": "#4285f4", "currency": "USD"},
    "AMZN":  {"name": "아마존",          "category": "클라우드 & AI", "color": "#ff9900", "currency": "USD"},
    "META":  {"name": "메타",            "category": "클라우드 & AI", "color": "#0668e1", "currency": "USD"},
}

# ETF 정의
ETFS = {
    "SMH":   {"name": "반도체 ETF",         "desc": "VanEck Semiconductor", "color": "#3b82f6"},
    "SOXX":  {"name": "반도체 ETF",         "desc": "iShares Semiconductor",  "color": "#6366f1"},
    "BOTZ":  {"name": "로보틱스 & AI ETF",  "desc": "Global X Robotics & AI", "color": "#10b981"},
    "AIQ":   {"name": "AI ETF",             "desc": "Global X AI & Tech",     "color": "#f59e0b"},
    "IGV":   {"name": "소프트웨어 ETF",     "desc": "iShares Software",       "color": "#ec4899"},
    "SKYY":  {"name": "클라우드 ETF",       "desc": "First Trust Cloud",      "color": "#06b6d4"},
    "QQQ":   {"name": "나스닥100 ETF",      "desc": "Invesco QQQ (벤치마크)",  "color": "#a855f7"},
    "SPY":   {"name": "S&P500 ETF",         "desc": "SPDR S&P 500 (벤치마크)", "color": "#71717a"},
}

DATA_DIR = Path(__file__).parent.parent / "data"


def fetch_prices(tickers: list[str], period: str = "13mo") -> dict[str, pd.Series]:
    """Yahoo Finance에서 종가 데이터 다운로드"""
    prices = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
            if df is not None and not df.empty:
                # yfinance 최신 버전 대응: MultiIndex 처리
                if isinstance(df.columns, pd.MultiIndex):
                    close = df[("Close", ticker)]
                else:
                    close = df["Close"]
                prices[ticker] = close.dropna()
                print(f"  ✓ {ticker}: {len(prices[ticker])}일치 데이터")
            else:
                print(f"  ✗ {ticker}: 데이터 없음")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    return prices


def calc_return(series: pd.Series, days: int) -> float | None:
    """n일 전 대비 수익률 계산"""
    if series is None or len(series) < days + 1:
        return None
    today = series.iloc[-1]
    past = series.iloc[-(days + 1)]
    if past == 0:
        return None
    return round(((today / past) - 1) * 100, 2)


def calc_ytd(series: pd.Series) -> float | None:
    """연초 대비 수익률"""
    if series is None or len(series) < 2:
        return None
    year_start = datetime(datetime.now().year, 1, 1)
    # 연초 이후 데이터만
    ytd_data = series[series.index >= pd.Timestamp(year_start)]
    if len(ytd_data) < 2:
        return None
    return round(((series.iloc[-1] / ytd_data.iloc[0]) - 1) * 100, 2)


def convert_krw_to_usd(krw_series: pd.Series, fx_series: pd.Series) -> pd.Series:
    """KRW 가격을 USD로 환산 (일별 환율 적용)"""
    # 날짜 인덱스 맞추기 (forward fill for holidays)
    combined = pd.DataFrame({"krw": krw_series, "fx": fx_series})
    combined["fx"] = combined["fx"].ffill().bfill()
    combined = combined.dropna()
    return combined["krw"] / combined["fx"]


def process_stocks(prices: dict, fx: pd.Series) -> dict:
    """종목별 수익률 계산"""
    result = {}
    for ticker, info in STOCKS.items():
        if ticker not in prices:
            print(f"  건너뜀: {ticker}")
            continue

        series = prices[ticker]

        # KRW 종목은 USD로 환산
        if info["currency"] == "KRW":
            series = convert_krw_to_usd(series, fx)
            if series is None or len(series) < 10:
                print(f"  건너뜀 (환산 실패): {ticker}")
                continue

        # 표시용 티커 (한국 종목은 이름으로)
        display_ticker = ticker.replace(".KS", "")
        if ticker == "005930.KS":
            display_ticker = "삼성전자"
        elif ticker == "000660.KS":
            display_ticker = "SK하이닉스"

        perf = {
            "1W": calc_return(series, 5),
            "1M": calc_return(series, 21),
            "3M": calc_return(series, 63),
            "YTD": calc_ytd(series),
            "12M": calc_return(series, 252),
        }
        # None → 0.0
        perf = {k: (v if v is not None else 0.0) for k, v in perf.items()}

        result[ticker] = {
            "ticker": ticker,
            "displayTicker": display_ticker,
            "name": info["name"],
            "category": info["category"],
            "color": info["color"],
            "currency": "USD",
            "currentPrice": round(float(series.iloc[-1]), 2) if len(series) > 0 else 0,
            "performance": perf,
        }
    return result


def process_etfs(prices: dict) -> dict:
    """ETF 수익률 계산"""
    result = {}
    for ticker, info in ETFS.items():
        if ticker not in prices:
            print(f"  건너뜀: {ticker}")
            continue

        series = prices[ticker]
        perf = {
            "1W": calc_return(series, 5),
            "1M": calc_return(series, 21),
            "3M": calc_return(series, 63),
            "YTD": calc_ytd(series),
            "12M": calc_return(series, 252),
        }
        perf = {k: (v if v is not None else 0.0) for k, v in perf.items()}

        result[ticker] = {
            "ticker": ticker,
            "name": info["name"],
            "desc": info["desc"],
            "color": info["color"],
            "currentPrice": round(float(series.iloc[-1]), 2) if len(series) > 0 else 0,
            "performance": perf,
        }
    return result


def main():
    print("=" * 50)
    print("AI/반도체 밸류체인 트래커 - 데이터 수집")
    print("=" * 50)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1) 모든 티커 + 환율 수집
    all_tickers = list(STOCKS.keys()) + list(ETFS.keys()) + ["KRW=X"]
    print(f"\n총 {len(all_tickers)}개 티커 다운로드 중...")
    prices = fetch_prices(all_tickers)

    # 2) 환율 데이터 확인
    if "KRW=X" not in prices:
        print("⚠️ 환율 데이터 가져오기 실패 — KRW 종목 제외됩니다")
        fx = None
    else:
        fx = prices.pop("KRW=X")
        print(f"  환율 최신: {fx.iloc[-1]:.2f} KRW/USD")

    # 3) 종목별 수익률 계산
    print("\n종목 수익률 계산 중...")
    stock_data = process_stocks(prices, fx)
    print(f"  → {len(stock_data)}개 종목 완료")

    # 4) ETF 수익률 계산
    print("\nETF 수익률 계산 중...")
    etf_data = process_etfs(prices)
    print(f"  → {len(etf_data)}개 ETF 완료")

    # 5) JSON 저장
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    valuechain_json = {
        "updated": now,
        "currency": "USD",
        "stocks": stock_data,
    }
    etf_json = {
        "updated": now,
        "etfs": etf_data,
    }

    vc_path = DATA_DIR / "valuechain.json"
    etf_path = DATA_DIR / "etf_compare.json"

    with open(vc_path, "w", encoding="utf-8") as f:
        json.dump(valuechain_json, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {vc_path} 저장 ({len(stock_data)}종목)")

    with open(etf_path, "w", encoding="utf-8") as f:
        json.dump(etf_json, f, ensure_ascii=False, indent=2)
    print(f"✓ {etf_path} 저장 ({len(etf_data)}개 ETF)")

    print("\n완료!")


if __name__ == "__main__":
    main()
