#!/usr/bin/env python3
"""
arXiv Paper Search Script for Video CNN Interpretability
自动搜索 arXiv 上的相关论文并生成 Markdown 格式总结
支持飞书通知和定时 GitHub Actions 运行
"""

import json
import os
import re
import ssl
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# Try to use arxiv API library, fallback to manual implementation
try:
    import arxiv
    USE_ARXIV_LIB = True
except ImportError:
    USE_ARXIV_LIB = False


def load_config(config_path: str) -> dict:
    """Load search configuration from JSON file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_feishu_config(config_path: str) -> dict:
    """Load Feishu configuration"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"enabled": False}


def escape_markdown(text: str) -> str:
    """Escape special markdown characters"""
    special_chars = ['*', '#', '`', '[', ']', '(', ')', '!', '-', '_']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


def extract_year_from_arxiv_id(arxiv_id: str) -> int:
    """Extract year from arXiv ID (e.g., 1711.11248 -> 2017)"""
    match = re.match(r'(\d{2})(\d{2})', arxiv_id.split('/')[-1][:4])
    if match:
        year_prefix = int(match.group(1))
        year_suffix = int(match.group(2))
        year = 2000 + year_prefix if year_prefix < 90 else 1900 + year_prefix
        if year_suffix <= 12:
            return year
        else:
            return year + 1
    return 2020


def search_arxiv_manual(query: str, max_results: int = 20) -> list:
    """Manual arXiv API search fallback"""
    base_url = 'http://export.arxiv.org/api/query?'
    search_query = f'all:{query}'
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    url = base_url + urlencode(params)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(url, timeout=30, context=ctx) as response:
            data = response.read().decode('utf-8')
            return parse_arxiv_response(data)
    except Exception as e:
        print(f"Error searching arXiv: {e}")
        return []


def parse_arxiv_response(xml_data: str) -> list:
    """Parse arXiv API XML response"""
    papers = []
    entries = re.findall(r'<entry>(.*?)</entry>', xml_data, re.DOTALL)
    for entry in entries:
        paper = {}
        title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        if title_match:
            paper['title'] = ' '.join(title_match.group(1).split())
        authors = re.findall(r'<name>(.*?)</name>', entry)
        paper['authors'] = authors if authors else ['Unknown']
        summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        if summary_match:
            paper['summary'] = ' '.join(summary_match.group(1).split())
        id_match = re.search(r'<id>(.*?)</id>', entry)
        if id_match:
            paper['arxiv_url'] = id_match.group(1)
            arxiv_id = id_match.group(1).split('/')[-1]
            paper['arxiv_id'] = arxiv_id
        published_match = re.search(r'<published>(.*?)</published>', entry)
        if published_match:
            paper['published'] = published_match.group(1)[:10]
        pdf_match = re.search(r'<link title="pdf" href="(.*?)"', entry)
        if pdf_match:
            paper['pdf_url'] = pdf_match.group(1)
        categories = re.findall(r'<category term="([^"]*)"', entry)
        paper['categories'] = [c for c in categories if c.startswith('cs.')]
        if paper.get('title'):
            papers.append(paper)
    return papers


def search_arxiv_with_lib(query: str, max_results: int = 20) -> list:
    """Search using arxiv library"""
    papers = []
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    for result in client.results(search):
        paper = {
            'title': result.title,
            'authors': [a.name for a in result.authors],
            'summary': result.summary,
            'arxiv_url': result.entry_id,
            'arxiv_id': result.get_short_id(),
            'published': result.published.strftime('%Y-%m-%d') if result.published else '',
            'pdf_url': result.pdf_url,
            'categories': [c.tag for c in result.categories]
        }
        papers.append(paper)
    return papers


def generate_paper_summary(paper: dict, category: str) -> str:
    """Generate improved markdown summary for a paper"""
    title = paper.get('title', 'Unknown Title')
    authors = ', '.join(paper.get('authors', ['Unknown']))
    arxiv_url = paper.get('arxiv_url', '#')
    arxiv_id = paper.get('arxiv_id', '')
    pdf_url = paper.get('pdf_url', '')
    published = paper.get('published', '')
    year = published[:4] if published else str(extract_year_from_arxiv_id(arxiv_id))

    # Generate one-sentence summary
    summary = paper.get('summary', '')[:800]
    one_sentence = summary.split('.')[0] + '.' if '.' in summary else summary[:200] + '...'

    # Extract key methods
    summary_text = summary[:500]

    md = f"""# {title}

**作者**: {authors}

**发表信息**: arXiv · {year}

**论文链接**: [arXiv:{arxiv_id}]({arxiv_url})

**代码链接**: (待补充)

---

### 🎯 一句话概括

> {one_sentence}

---

### 📖 方法论

#### 核心思想
{summary_text}

---

### 📊 实验

**数据集**: (待补充)

**主要结果**: (待补充)

---

### 💡 总结与思考

**论文贡献**: (待整理)

**局限性**: (待分析)

---

### 🔄 后续改进方向

1. (待分析)
2. (待分析)

---

**整理信息**
- 整理时间: {datetime.now().strftime('%Y-%m-%d')}
- 分类: `{"核心领域" if category == "core" else "相关领域"}`
- arXiv ID: {arxiv_id}
"""
    return md


def save_paper(paper: dict, output_dir: str, category: str) -> str:
    """Save paper summary to file"""
    published = paper.get('published', '')
    year = published[:4] if published else str(extract_year_from_arxiv_id(paper.get('arxiv_id', '')))
    year_dir = os.path.join(output_dir, year, category)
    os.makedirs(year_dir, exist_ok=True)

    title = paper.get('title', 'unknown')
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = re.sub(r'\s+', '-', safe_title)[:50]
    filename = f"{safe_title}.md"

    filepath = os.path.join(year_dir, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{safe_title}-{counter}.md"
        filepath = os.path.join(year_dir, filename)
        counter += 1

    content = generate_paper_summary(paper, category)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath


def send_feishu_notification(new_papers: list, webhook_url: str):
    """Send notification to Feishu"""
    if not new_papers or not webhook_url:
        return

    # Prepare paper list for Feishu
    paper_list = []
    for paper in new_papers[:10]:  # Max 10 papers per notification
        title = paper.get('title', 'Unknown')[:40]
        arxiv_id = paper.get('arxiv_id', '')
        url = paper.get('arxiv_url', '#')
        paper_list.append(f"- [{title}...]({url})")

    content = f"""📚 **视频 CNN 可解释性论文更新**

本周新增 **{len(new_papers)}** 篇论文！

{paper_list}

---
🤖 由 GitHub Actions 自动推送"""
    if len(new_papers) > 10:
        content += f"\n\n_还有 {len(new_papers) - 10} 篇论文..."

    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request(webhook_url, data=data, headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=10) as response:
            print(f"  Feishu notification sent: {response.status}")
    except Exception as e:
        print(f"  Feishu notification failed: {e}")


def get_existing_papers(papers_dir: str) -> set:
    """Get set of existing paper arxiv IDs to avoid duplicates"""
    existing = set()
    if os.path.exists(papers_dir):
        for root, dirs, files in os.walk(papers_dir):
            for file in files:
                if file.endswith('.md') and file != 'README.md':
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Extract arxiv ID from file content
                            match = re.search(r'arXiv ID: (\S+)', content)
                            if match:
                                existing.add(match.group(1))
                    except:
                        pass
    return existing


def generate_readme(output_dir: str, papers: list):
    """Generate improved README with table"""
    # Group by year and category
    by_year = {}
    for paper in papers:
        published = paper.get('published', '')
        year = published[:4] if published else 'unknown'
        if year not in by_year:
            by_year[year] = {'core': [], 'related': []}
        category = paper.get('search_category', 'related')
        by_year[year][category].append(paper)

    # Build table content
    table_rows = []
    for year in sorted(by_year.keys(), reverse=True):
        for category in ['core', 'related']:
            papers_in_cat = by_year[year][category]
            if not papers_in_cat:
                continue
            category_label = '🔥 核心' if category == 'core' else '📎 相关'
            for paper in sorted(papers_in_cat, key=lambda x: x.get('title', '')):
                title = paper.get('title', 'Unknown')[:45]
                arxiv_url = paper.get('arxiv_url', '#')
                arxiv_id = paper.get('arxiv_id', '')
                authors = paper.get('authors', [])[:2]
                authors_str = ', '.join(authors) + ('+' if len(paper.get('authors', [])) > 2 else '')

                # Find the file path
                safe_title = re.sub(r'[^\w\s-]', '', paper.get('title', 'unknown'))
                safe_title = re.sub(r'\s+', '-', safe_title)[:50]
                md_file = f"papers/{year}/{category}/{safe_title}.md"

                table_rows.append(f"| {year} | [{title}]({md_file}) | {authors_str} | {category_label} |")

    # Generate README
    readme = f"""# 📚 视频 CNN 可解释性论文库

> 自动化论文搜索与整理系统 | 专注于 3DCNN、R(2+1)D 模型及可解释性研究

[![GitHub Actions](https://github.com/MSWEIMZ/video-cnn-interpretability/actions/workflows/arxiv_search.yml/badge.svg)](https://github.com/MSWEIMZ/video-cnn-interpretability/actions)

## 📊 论文统计

- **总计**: {len(papers)} 篇论文
- **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 搜索领域

### 核心领域
- R(2+1)D video classification interpretability
- 3D CNN video explainability
- Spatiotemporal convolution video understanding

### 相关领域
- CNN interpretability explainability
- Network dissection deep vision
- Attention mechanism visualization

---

## 📋 论文列表

| 年份 | 标题 | 作者 | 分类 |
|------|------|------|------|
{chr(10).join(table_rows) if table_rows else "| - | - | - | - |"}

---

## 📁 项目结构

```
video-cnn-interpretability/
├── arxiv_search.py          # arXiv 搜索脚本
├── search_config.json       # 搜索配置文件
├── feishu_config.json       # 飞书通知配置
├── paper_template.md        # 论文总结模板
├── papers/                  # 论文总结 (按年份/分类)
│   ├── 2024/
│   │   ├── core/          # 核心领域论文
│   │   └── related/       # 相关领域论文
│   └── ...
└── README.md              # 本文件
```

## ⚙️ 自动更新

本项目通过 **GitHub Actions** 每周自动：
1. 搜索 arXiv 最新相关论文
2. 生成论文总结
3. 更新本 README
4. 推送更新到 GitHub
5. 发送飞书群通知

## 🤝 贡献

欢迎：
- 补充论文详情（方法论、实验结果等）
- 修正论文分类
- 提供代码链接

## 📄 License

仅供学术研究使用
"""
    index_path = os.path.join(output_dir, '..', 'README.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"  README updated: {index_path}")


def main():
    """Main search function"""
    script_dir = Path(__file__).parent.absolute()
    config_path = script_dir / 'search_config.json'
    feishu_config_path = script_dir / 'feishu_config.json'
    output_dir = script_dir / 'papers'

    print("=" * 60)
    print("Video CNN Interpretability Paper Search")
    print("=" * 60)

    config = load_config(str(config_path))
    feishu_config = load_feishu_config(str(feishu_config_path))
    queries = config.get('search_queries', {})
    max_results = config.get('max_results_per_query', 20)

    all_papers = []

    # Search core queries
    print("\n[核心领域搜索]")
    for query in queries.get('core', []):
        print(f"\nSearching: {query}")
        if USE_ARXIV_LIB:
            papers = search_arxiv_with_lib(query, max_results)
        else:
            papers = search_arxiv_manual(query, max_results)
        print(f"  Found {len(papers)} papers")
        for paper in papers:
            paper['search_category'] = 'core'
            paper['search_query'] = query
        all_papers.extend(papers)

    # Search related queries
    print("\n[相关领域搜索]")
    for query in queries.get('related', []):
        print(f"\nSearching: {query}")
        if USE_ARXIV_LIB:
            papers = search_arxiv_with_lib(query, max_results)
        else:
            papers = search_arxiv_manual(query, max_results)
        print(f"  Found {len(papers)} papers")
        for paper in papers:
            paper['search_category'] = 'related'
            paper['search_query'] = query
        all_papers.extend(papers)

    # Deduplicate by arxiv ID
    seen_ids = set()
    unique_papers = []
    for paper in all_papers:
        paper_id = paper.get('arxiv_id', '')
        if paper_id and paper_id not in seen_ids:
            seen_ids.add(paper_id)
            unique_papers.append(paper)

    print(f"\n总计找到 {len(unique_papers)} 篇不重复论文")

    # Check for existing papers
    existing_ids = get_existing_papers(str(output_dir))
    new_papers = [p for p in unique_papers if p.get('arxiv_id') not in existing_ids]
    print(f"新增论文: {len(new_papers)} 篇")

    # Save new papers
    print("\n[保存论文]")
    saved_files = []
    for paper in unique_papers:
        category = paper.get('search_category', 'related')
        filepath = save_paper(paper, str(output_dir), category)
        saved_files.append(filepath)

    # Update README
    print("\n[更新 README]")
    generate_readme(str(output_dir), unique_papers)

    # Send Feishu notification for new papers
    if new_papers and feishu_config.get('enabled'):
        print("\n[发送飞书通知]")
        send_feishu_notification(new_papers, feishu_config.get('feishu_webhook', ''))

    print(f"\n完成！已保存 {len(saved_files)} 篇论文")


if __name__ == '__main__':
    main()
