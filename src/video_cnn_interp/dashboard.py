"""看板页面生成模块"""
from __future__ import annotations
import json
from datetime import datetime
from collections import defaultdict


def generate_dashboard_html(records: list[dict], stats: dict) -> str:
    """生成完整的 HTML 看板页面"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = stats.get("total", len(records))
    by_label = stats.get("by_label", {})

    by_year: dict[int, int] = defaultdict(int)
    for r in records:
        by_year[r.get("year", 0)] += 1
    years = sorted(by_year.keys(), reverse=True)

    by_topic: dict[str, int] = defaultdict(int)
    for r in records:
        for t in r.get("topics", []):
            by_topic[t] += 1

    year_data = [{"year": y, "count": by_year[y]} for y in sorted(by_year.keys())]
    year_json = json.dumps(year_data, ensure_ascii=False)

    topic_data = [{"topic": t, "count": c} for t, c in sorted(by_topic.items(), key=lambda x: -x[1])][:10]
    topic_json = json.dumps(topic_data, ensure_ascii=False)

    recent = sorted(records, key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))[:50]
    recent_rows = []
    for r in recent:
        label = r.get("quality_label", "")
        icon = {"core": "🔥", "strongly_related": "📎", "weakly_related": "📝"}.get(label, "📝")
        recent_rows.append({
            "icon": icon,
            "title": r.get("title", "")[:80],
            "year": r.get("year", ""),
            "score": r.get("relevance_score", 0),
            "label": label,
            "url": r.get("url", "#"),
            "method_type": r.get("method_type", ""),
            "relation": r.get("relation_to_r2plus1d", ""),
        })
    recent_json = json.dumps(recent_rows, ensure_ascii=False)

    core_papers = [r for r in records if r.get("quality_label") == "core"]
    core_papers.sort(key=lambda r: (-r.get("year", 0), -r.get("relevance_score", 0)))
    core_rows = []
    for r in core_papers[:20]:
        core_rows.append({
            "icon": "🔥",
            "title": r.get("title", "")[:80],
            "year": r.get("year", ""),
            "score": r.get("relevance_score", 0),
            "url": r.get("url", "#"),
            "method_type": r.get("method_type", ""),
        })
    core_json = json.dumps(core_rows, ensure_ascii=False)

    html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>视频 CNN 可解释性论文库 - 看板</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;color:#333}
.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:2rem;text-align:center}
.header h1{font-size:1.8rem;margin-bottom:.5rem}
.header p{opacity:.9;font-size:.95rem}
.container{max-width:1200px;margin:0 auto;padding:1.5rem}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}
.stat-card{background:#fff;border-radius:12px;padding:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center}
.stat-card .number{font-size:2rem;font-weight:700;color:#667eea}
.stat-card .label{font-size:.85rem;color:#888;margin-top:.3rem}
.section{background:#fff;border-radius:12px;padding:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:1.5rem}
.section h2{font-size:1.2rem;margin-bottom:1rem;color:#333;border-left:4px solid #667eea;padding-left:.8rem}
.bar-chart{display:flex;align-items:flex-end;gap:4px;height:220px;padding:0 1rem}
.bar{background:linear-gradient(to top,#667eea,#764ba2);border-radius:4px 4px 0 0;min-width:18px;flex:1;position:relative;transition:all .3s;cursor:pointer}
.bar:hover{opacity:.8}
.bar .tip{display:none;position:absolute;top:-28px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:2px 8px;border-radius:4px;font-size:.72rem;white-space:nowrap}
.bar:hover .tip{display:block}
.bar-labels{display:flex;gap:4px;padding:.5rem 1rem}
.bar-labels span{flex:1;text-align:center;font-size:.68rem;color:#888}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th{background:#f8f9fa;padding:.65rem;text-align:left;font-weight:600;border-bottom:2px solid #e9ecef}
td{padding:.55rem .65rem;border-bottom:1px solid #f0f0f0}
tr:hover{background:#f8f9ff}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.72rem;font-weight:500}
.badge-core{background:#fff3e0;color:#e65100}
.badge-strongly_related{background:#e3f2fd;color:#1565c0}
.badge-weakly_related{background:#f3e5f5;color:#7b1fa2}
a{color:#667eea;text-decoration:none}
a:hover{text-decoration:underline}
.footer{text-align:center;padding:2rem;color:#aaa;font-size:.8rem}
.filter-bar{display:flex;gap:.8rem;margin-bottom:1rem;flex-wrap:wrap}
.fbtn{padding:.4rem 1rem;border:1px solid #ddd;border-radius:20px;background:#fff;cursor:pointer;font-size:.82rem;transition:all .2s}
.fbtn:hover,.fbtn.active{background:#667eea;color:#fff;border-color:#667eea}
</style>
</head>
<body>
<div class="header">
<h1>视频 CNN 可解释性论文库</h1>
<p>自动化论文搜索与整理 | 3DCNN / R(2+1)D / 可解释性</p>
<p style="margin-top:.5rem;opacity:.7">最后更新: NOW_PLACEHOLDER</p>
</div>
<div class="container">
<div class="stats-grid">
<div class="stat-card"><div class="number">TOTAL_PLACEHOLDER</div><div class="label">论文总数</div></div>
<div class="stat-card"><div class="number">CORE_PLACEHOLDER</div><div class="label">核心论文</div></div>
<div class="stat-card"><div class="number">STRONG_PLACEHOLDER</div><div class="label">高相关</div></div>
<div class="stat-card"><div class="number">WEAK_PLACEHOLDER</div><div class="label">弱相关</div></div>
<div class="stat-card"><div class="number">YEARS_PLACEHOLDER</div><div class="label">跨越年份</div></div>
</div>
<div class="section"><h2>年份分布</h2><div class="bar-chart" id="yc"></div><div class="bar-labels" id="yl"></div></div>
<div class="section"><h2>核心论文 Top 20</h2><table><thead><tr><th></th><th>标题</th><th>年份</th><th>分数</th><th>方法</th></tr></thead><tbody id="ct"></tbody></table></div>
<div class="section"><h2>最新论文 Top 50</h2><div class="filter-bar"><button class="fbtn active" onclick="ft('all',this)">全部</button><button class="fbtn" onclick="ft('core',this)">核心</button><button class="fbtn" onclick="ft('strongly_related',this)">高相关</button><button class="fbtn" onclick="ft('weakly_related',this)">弱相关</button></div><table><thead><tr><th></th><th>标题</th><th>年份</th><th>分数</th><th>方法</th><th>与R(2+1)D关系</th></tr></thead><tbody id="rt"></tbody></table></div>
</div>
<div class="footer">视频 CNN 可解释性论文库 v2.0 | 自动生成</div>
<script>
const YD=YEAR_JSON, RD=RECENT_JSON, CD=CORE_JSON;
const mx=Math.max(...YD.map(d=>d.count));
const yc=document.getElementById('yc'),yl=document.getElementById('yl');
YD.forEach(d=>{const b=document.createElement('div');b.className='bar';b.style.height=(d.count/mx*100)+'%';b.innerHTML='<span class="tip">'+d.year+': '+d.count+'</span>';yc.appendChild(b);const l=document.createElement('span');l.textContent=d.year;yl.appendChild(l)});
const ct=document.getElementById('ct');
CD.forEach(r=>{ct.innerHTML+='<tr><td>'+r.icon+'</td><td><a href="'+r.url+'" target="_blank">'+r.title+'</a></td><td>'+r.year+'</td><td>'+r.score+'</td><td>'+r.method_type+'</td></tr>'});
const rt=document.getElementById('rt');
function rr(data){rt.innerHTML='';data.forEach(r=>{rt.innerHTML+='<tr data-l="'+r.label+'"><td><span class="badge badge-'+r.label+'">'+r.icon+'</span></td><td><a href="'+r.url+'" target="_blank">'+r.title+'</a></td><td>'+r.year+'</td><td>'+r.score+'</td><td>'+r.method_type+'</td><td>'+r.relation+'</td></tr>'})}
rr(RD);
function ft(l,btn){document.querySelectorAll('.fbtn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');l==='all'?rr(RD):rr(RD.filter(r=>r.label===l))}
</script>
</body>
</html>"""
    html = html.replace("NOW_PLACEHOLDER", now)
    html = html.replace("TOTAL_PLACEHOLDER", str(total))
    html = html.replace("CORE_PLACEHOLDER", str(by_label.get("core", 0)))
    html = html.replace("STRONG_PLACEHOLDER", str(by_label.get("strongly_related", 0)))
    html = html.replace("WEAK_PLACEHOLDER", str(by_label.get("weakly_related", 0)))
    html = html.replace("YEARS_PLACEHOLDER", str(len(years)))
    html = html.replace("YEAR_JSON", year_json)
    html = html.replace("RECENT_JSON", recent_json)
    html = html.replace("CORE_JSON", core_json)
    return html
