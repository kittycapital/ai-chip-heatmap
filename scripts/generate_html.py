#!/usr/bin/env python3
"""
AI/반도체 밸류체인 트래커 - HTML 생성
valuechain.html: 밸류체인별 히트맵
etf_compare.html: AI/반도체 테마 ETF 성과 비교
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"

SHARE_URL = "https://herdvibe.com/108"

# ── 공통 CSS 변수 + 폰트 ────────────────────────────────
COMMON_HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">"""

COMMON_CSS = """
:root {
    --bg:#000;--surface:#0a0a0a;--surface2:#111;--border:#1a1a1a;
    --border-hover:#2a2a2a;--text:#e4e4e7;--text-dim:#71717a;--text-muted:#52525b;
    --green:#22c55e;--red:#ef4444;--cyan:#22d3ee;
    --mono:'JetBrains Mono',monospace;--sans:'Noto Sans KR',-apple-system,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scrollbar-width:none}html::-webkit-scrollbar{display:none}
body{background:var(--bg);color:var(--text);font-family:var(--sans);
    min-height:100vh;-webkit-font-smoothing:antialiased}
.container{max-width:960px;margin:0 auto;width:100%;padding:0 16px}
.header{padding:24px 20px 12px;text-align:center}
.header h1{font-size:clamp(18px,4vw,26px);font-weight:800;color:#fff;letter-spacing:-0.02em;margin-bottom:4px}
.sub{font-size:12px;color:var(--text-dim)}
.time{font-family:var(--mono);font-size:10px;color:var(--text-muted);margin-top:6px}

/* Share buttons */
.share-bar{display:flex;justify-content:center;flex-wrap:wrap;gap:6px;padding:12px 0}
.share-btn{display:inline-flex;align-items:center;gap:4px;
    padding:5px 10px;border:1px solid var(--border);border-radius:6px;
    background:var(--surface);color:var(--text-dim);font:500 11px var(--sans);
    cursor:pointer;transition:all .2s;text-decoration:none}
.share-btn:hover{border-color:var(--border-hover);color:var(--text);background:var(--surface2)}

/* Sort controls */
.sort-controls{display:flex;justify-content:center;gap:4px;padding:12px 0}
.sort-btn{padding:5px 10px;border:1px solid var(--border);background:var(--surface);
    color:var(--text-dim);font:500 11px var(--sans);cursor:pointer;border-radius:6px;transition:all .2s}
.sort-btn.active{background:var(--cyan);color:#000;font-weight:600;border-color:var(--cyan)}

/* Category header */
.cat-row td{padding:8px 12px;font:600 11px var(--sans);color:var(--cyan);
    letter-spacing:0.05em;border-bottom:1px solid var(--border)}

/* Legend */
.legend-bar{display:flex;align-items:center;justify-content:center;gap:8px;padding:16px 0 8px}
.legend-gradient{width:200px;height:8px;border-radius:4px;
    background:linear-gradient(to right,#dc2626,#7f1d1d,#1a1a1a,#14532d,#16a34a)}
.legend-label{font:400 10px var(--mono);color:var(--text-muted)}

/* Footer */
.footer{padding:16px;text-align:center;font:400 10px var(--sans);color:var(--text-muted);border-top:1px solid var(--border);margin-top:12px}

/* Toast */
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(100px);
    background:#22d3ee;color:#000;padding:8px 20px;border-radius:8px;font:600 12px var(--sans);
    opacity:0;transition:all .3s;z-index:999;pointer-events:none}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
"""

SHARE_BUTTONS_HTML = f"""<div class="share-bar">
    <a class="share-btn" href="https://twitter.com/intent/tweet?url={SHARE_URL}&text=AI%2F%EB%B0%98%EB%8F%84%EC%B2%B4%20%EB%B0%B8%EB%A5%98%EC%B2%B4%EC%9D%B8%20%ED%8A%B8%EB%9E%98%EC%BB%A4" target="_blank" rel="noopener">𝕏 트위터</a>
    <a class="share-btn" href="https://story.kakao.com/share?url={SHARE_URL}" target="_blank" rel="noopener">● 카카오톡</a>
    <a class="share-btn" href="https://t.me/share/url?url={SHARE_URL}&text=AI%2F%EB%B0%98%EB%8F%84%EC%B2%B4%20%EB%B0%B8%EB%A5%98%EC%B2%B4%EC%9D%B8%20%ED%8A%B8%EB%9E%98%EC%BB%A4" target="_blank" rel="noopener">✈ 텔레그램</a>
    <a class="share-btn" onclick="copyLink()" style="cursor:pointer">📋 인스타그램</a>
    <a class="share-btn" onclick="copyLink()" style="cursor:pointer">🔗 링크복사</a>
</div>"""

COPY_JS = f"""
function copyLink(){{
    var t='{SHARE_URL}';
    if(navigator.clipboard&&navigator.clipboard.writeText){{
        navigator.clipboard.writeText(t).then(function(){{showToast()}});
    }}else{{
        try{{window.parent.postMessage({{type:'clipboard',text:t}},'*');showToast()}}catch(e){{}}
    }}
}}
function showToast(){{
    var el=document.getElementById('toast');el.classList.add('show');
    setTimeout(function(){{el.classList.remove('show')}},2000);
}}
"""

CATEGORY_ORDER = ["설계", "제조", "장비", "메모리", "AI 인프라", "클라우드 & AI"]


# ── 밸류체인 히트맵 ──────────────────────────────────────
def generate_valuechain():
    data_path = DATA_DIR / "valuechain.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = data.get("updated", "")
    stocks = data.get("stocks", {})

    # 종목을 JSON으로 JS에 전달
    stocks_json = json.dumps(stocks, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
{COMMON_HEAD}
<title>AI/반도체 밸류체인 히트맵 | HerdVibe</title>
<style>
{COMMON_CSS}

.heatmap-table{{width:100%;border-collapse:separate;border-spacing:3px}}
.heatmap-table th{{font:600 11px var(--mono);color:var(--text-muted);padding:8px 4px;text-align:center}}
.heatmap-table th.stock-header{{text-align:left;padding-left:12px;min-width:140px}}
.heatmap-table td{{text-align:center;padding:0;border-radius:6px;height:42px;
    transition:transform .15s,box-shadow .15s;position:relative}}
.heatmap-table td:hover{{transform:scale(1.05);box-shadow:0 0 12px rgba(255,255,255,.08);z-index:2}}
.heatmap-table td.stock-cell{{background:transparent;text-align:left;padding-left:12px}}
.heatmap-table td.stock-cell:hover{{transform:none;box-shadow:none}}
.stock-name{{display:flex;align-items:center;gap:8px}}
.stock-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.stock-label{{font:500 12px var(--sans);color:var(--text);white-space:nowrap}}
.stock-ticker{{font:400 12px var(--mono);color:var(--text-muted)}}
.cell-value{{font:700 13px var(--mono);position:relative;z-index:1}}

@media(max-width:600px){{
    .heatmap-table th{{font-size:9px;padding:6px 2px}}
    .heatmap-table th.stock-header{{min-width:100px}}
    .stock-label{{font-size:11px}}
    .stock-ticker{{font-size:11px}}
    .cell-value{{font-size:11px}}
    .heatmap-table td{{height:38px}}
    .container{{padding:0 8px}}
}}
</style>
</head>
<body>

<div class="header">
    <h1>AI/반도체 밸류체인 히트맵</h1>
    <div class="sub">공정별 22개 핵심 종목 · 기간별 수익률 한눈에 비교 (USD 기준)</div>
    <div class="time">마지막 업데이트: {updated}</div>
</div>

{SHARE_BUTTONS_HTML}

<div class="container">
    <div class="sort-controls">
        <button class="sort-btn" data-sort="1W">1W 정렬</button>
        <button class="sort-btn active" data-sort="1M">1M 정렬</button>
        <button class="sort-btn" data-sort="3M">3M 정렬</button>
        <button class="sort-btn" data-sort="YTD">YTD 정렬</button>
        <button class="sort-btn" data-sort="12M">12M 정렬</button>
    </div>

    <table class="heatmap-table">
        <thead>
            <tr>
                <th class="stock-header">종목</th>
                <th>1W</th><th>1M</th><th>3M</th><th>YTD</th><th>12M</th>
            </tr>
        </thead>
        <tbody id="heatmap-body"></tbody>
    </table>

    <div class="legend-bar">
        <span class="legend-label">-30%</span>
        <div class="legend-gradient"></div>
        <span class="legend-label">+30%</span>
    </div>
</div>

<div class="footer">
    데이터 출처: Yahoo Finance · 한국 종목은 USD 환산 기준 · 투자 판단은 본인의 책임입니다
</div>

<div class="toast" id="toast">링크가 복사되었습니다</div>

<script>
{COPY_JS}

const STOCKS = {stocks_json};
const CATEGORIES = {json.dumps(CATEGORY_ORDER, ensure_ascii=False)};
const periods = ['1W','1M','3M','YTD','12M'];
let currentSort = '1M';

function getColor(value) {{
    const clamped = Math.max(-30, Math.min(30, value));
    const ratio = (clamped + 30) / 60;
    if (ratio < 0.5) {{
        const t = ratio / 0.5;
        return `rgb(${{Math.round(220 - t*100)}}, ${{Math.round(38 + t*20)}}, ${{Math.round(38 + t*20)}})`;
    }} else {{
        const t = (ratio - 0.5) / 0.5;
        return `rgb(${{Math.round(58 - t*36)}}, ${{Math.round(58 + t*105)}}, ${{Math.round(58 - t*20)}})`;
    }}
}}

function render() {{
    const tbody = document.getElementById('heatmap-body');
    let html = '';

    CATEGORIES.forEach(cat => {{
        // 해당 카테고리 종목 필터 + 정렬
        const items = Object.entries(STOCKS)
            .filter(([_, s]) => s.category === cat)
            .sort((a, b) => b[1].performance[currentSort] - a[1].performance[currentSort]);

        if (items.length === 0) return;

        // 카테고리 헤더 행
        html += `<tr class="cat-row"><td colspan="6">${{cat}}</td></tr>`;

        items.forEach(([ticker, s]) => {{
            const cells = periods.map(p => {{
                const val = s.performance[p];
                const bg = getColor(val);
                const sign = val >= 0 ? '+' : '';
                const alpha = Math.abs(val) > 10 ? 0.95 : Math.abs(val) > 4 ? 0.8 : 0.6;
                return `<td style="background:${{bg}}"><span class="cell-value" style="color:rgba(255,255,255,${{alpha}})">${{sign}}${{val.toFixed(1)}}%</span></td>`;
            }}).join('');

            html += `<tr>
                <td class="stock-cell">
                    <div class="stock-name">
                        <div class="stock-dot" style="background:${{s.color}}"></div>
                        <span class="stock-label">${{s.name}}</span>
                        <span class="stock-ticker">${{s.displayTicker}}</span>
                    </div>
                </td>
                ${{cells}}
            </tr>`;
        }});
    }});

    tbody.innerHTML = html;
}}

document.querySelectorAll('.sort-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSort = btn.dataset.sort;
        render();
    }});
}});

render();
</script>
</body>
</html>"""

    out_path = ROOT_DIR / "valuechain.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} 생성 ({len(stocks)}종목)")


# ── ETF 비교 ──────────────────────────────────────────────
def generate_etf_compare():
    data_path = DATA_DIR / "etf_compare.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = data.get("updated", "")
    etfs = data.get("etfs", {})
    etfs_json = json.dumps(etfs, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
{COMMON_HEAD}
<title>AI/반도체 테마 ETF 비교 | HerdVibe</title>
<style>
{COMMON_CSS}

.etf-table{{width:100%;border-collapse:separate;border-spacing:3px}}
.etf-table th{{font:600 11px var(--mono);color:var(--text-muted);padding:8px 4px;text-align:center}}
.etf-table th.etf-header{{text-align:left;padding-left:12px;min-width:180px}}
.etf-table td{{text-align:center;padding:0;border-radius:6px;height:48px;
    transition:transform .15s,box-shadow .15s;position:relative}}
.etf-table td:hover{{transform:scale(1.05);box-shadow:0 0 12px rgba(255,255,255,.08);z-index:2}}
.etf-table td.etf-cell{{background:transparent;text-align:left;padding-left:12px}}
.etf-table td.etf-cell:hover{{transform:none;box-shadow:none}}
.etf-info{{display:flex;flex-direction:column;gap:2px}}
.etf-name{{display:flex;align-items:center;gap:8px}}
.etf-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.etf-ticker{{font:600 13px var(--mono);color:var(--text)}}
.etf-label{{font:400 11px var(--sans);color:var(--text-dim)}}
.etf-desc{{font:400 10px var(--sans);color:var(--text-muted);padding-left:16px}}
.cell-value{{font:700 14px var(--mono);position:relative;z-index:1}}
.etf-price{{font:400 11px var(--mono);color:var(--text-dim);padding-left:16px;margin-top:1px}}

@media(max-width:600px){{
    .etf-table th{{font-size:9px;padding:6px 2px}}
    .etf-table th.etf-header{{min-width:130px}}
    .etf-ticker{{font-size:11px}}
    .etf-label{{font-size:10px}}
    .etf-desc{{display:none}}
    .etf-price{{display:none}}
    .cell-value{{font-size:11px}}
    .etf-table td{{height:42px}}
    .container{{padding:0 8px}}
}}
</style>
</head>
<body>

<div class="header">
    <h1>AI/반도체 테마 ETF 성과 비교</h1>
    <div class="sub">반도체 · AI · 클라우드 · 로보틱스 ETF 수익률 비교</div>
    <div class="time">마지막 업데이트: {updated}</div>
</div>

{SHARE_BUTTONS_HTML}

<div class="container">
    <div class="sort-controls">
        <button class="sort-btn" data-sort="1W">1W 정렬</button>
        <button class="sort-btn active" data-sort="1M">1M 정렬</button>
        <button class="sort-btn" data-sort="3M">3M 정렬</button>
        <button class="sort-btn" data-sort="YTD">YTD 정렬</button>
        <button class="sort-btn" data-sort="12M">12M 정렬</button>
    </div>

    <table class="etf-table">
        <thead>
            <tr>
                <th class="etf-header">ETF</th>
                <th>1W</th><th>1M</th><th>3M</th><th>YTD</th><th>12M</th>
            </tr>
        </thead>
        <tbody id="etf-body"></tbody>
    </table>

    <div class="legend-bar">
        <span class="legend-label">-20%</span>
        <div class="legend-gradient"></div>
        <span class="legend-label">+20%</span>
    </div>
</div>

<div class="footer">
    데이터 출처: Yahoo Finance · QQQ/SPY는 벤치마크 비교용 · 투자 판단은 본인의 책임입니다
</div>

<div class="toast" id="toast">링크가 복사되었습니다</div>

<script>
{COPY_JS}

const ETFS = {etfs_json};
const periods = ['1W','1M','3M','YTD','12M'];
let currentSort = '1M';

function getColor(value) {{
    const clamped = Math.max(-20, Math.min(20, value));
    const ratio = (clamped + 20) / 40;
    if (ratio < 0.5) {{
        const t = ratio / 0.5;
        return `rgb(${{Math.round(220 - t*100)}}, ${{Math.round(38 + t*20)}}, ${{Math.round(38 + t*20)}})`;
    }} else {{
        const t = (ratio - 0.5) / 0.5;
        return `rgb(${{Math.round(58 - t*36)}}, ${{Math.round(58 + t*105)}}, ${{Math.round(58 - t*20)}})`;
    }}
}}

function render() {{
    const tbody = document.getElementById('etf-body');
    const sorted = Object.entries(ETFS)
        .sort((a, b) => b[1].performance[currentSort] - a[1].performance[currentSort]);

    tbody.innerHTML = sorted.map(([ticker, e]) => {{
        const cells = periods.map(p => {{
            const val = e.performance[p];
            const bg = getColor(val);
            const sign = val >= 0 ? '+' : '';
            const alpha = Math.abs(val) > 8 ? 0.95 : Math.abs(val) > 3 ? 0.8 : 0.6;
            return `<td style="background:${{bg}}"><span class="cell-value" style="color:rgba(255,255,255,${{alpha}})">${{sign}}${{val.toFixed(1)}}%</span></td>`;
        }}).join('');

        return `<tr>
            <td class="etf-cell">
                <div class="etf-info">
                    <div class="etf-name">
                        <div class="etf-dot" style="background:${{e.color}}"></div>
                        <span class="etf-ticker">${{ticker}}</span>
                        <span class="etf-label">${{e.name}}</span>
                    </div>
                    <div class="etf-desc">${{e.desc}} · $${{e.currentPrice.toFixed(2)}}</div>
                </div>
            </td>
            ${{cells}}
        </tr>`;
    }}).join('');
}}

document.querySelectorAll('.sort-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSort = btn.dataset.sort;
        render();
    }});
}});

render();
</script>
</body>
</html>"""

    out_path = ROOT_DIR / "etf_compare.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} 생성 ({len(etfs)}개 ETF)")


def main():
    print("HTML 생성 중...")
    generate_valuechain()
    generate_etf_compare()
    print("완료!")


if __name__ == "__main__":
    main()
