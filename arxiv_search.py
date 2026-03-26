#!/usr/bin/env python3
"""
arXiv Paper Search Script for Video CNN Interpretability
自动搜索 arXiv 上的相关论文并生成 Markdown 格式总结
"""

import json
import os
import re
import ssl
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
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


def escape_markdown(text: str) -> str:
    """Escape special markdown characters"""
    special_chars = ['*', '#', '`', '[', ']', '(', ')', '!']
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

    # Build search query
    search_query = f'all:{query}'
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }

    url = base_url + urlencode(params)

    # Create SSL context that doesn't verify certificates
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

    # Simple XML parsing without lxml
    entries = re.findall(r'<entry>(.*?)</entry>', xml_data, re.DOTALL)

    for entry in entries:
        paper = {}

        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        if title_match:
            paper['title'] = ' '.join(title_match.group(1).split())

        # Extract authors
        authors = re.findall(r'<name>(.*?)</name>', entry)
        paper['authors'] = authors if authors else ['Unknown']

        # Extract summary
        summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        if summary_match:
            paper['summary'] = ' '.join(summary_match.group(1).split())

        # Extract arXiv ID
        id_match = re.search(r'<id>(.*?)</id>', entry)
        if id_match:
            paper['arxiv_url'] = id_match.group(1)
            arxiv_id = id_match.group(1).split('/')[-1]
            paper['arxiv_id'] = arxiv_id

        # Extract published date
        published_match = re.search(r'<published>(.*?)</published>', entry)
        if published_match:
            paper['published'] = published_match.group(1)[:10]

        # Extract PDF link
        pdf_match = re.search(r'<link title="pdf" href="(.*?)"', entry)
        if pdf_match:
            paper['pdf_url'] = pdf_match.group(1)

        # Extract categories
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
    """Generate markdown summary for a paper"""
    title = escape_markdown(paper.get('title', 'Unknown Title'))
    authors = ', '.join(paper.get('authors', ['Unknown']))
    arxiv_url = paper.get('arxiv_url', '#')
    arxiv_id = paper.get('arxiv_id', '')
    pdf_url = paper.get('pdf_url', '')

    # Extract year from published date or arxiv ID
    published = paper.get('published', '')
    year = published[:4] if published else str(extract_year_from_arxiv_id(arxiv_id))

    # Generate one-sentence summary
    summary = paper.get('summary', '')[:500]
    one_sentence = summary.split('.')[0] + '.' if '.' in summary else summary[:200] + '...'

    md = f"""## {title}

**基本信息**
- **作者**: {authors}
- **发表**: arXiv:{year}
- **arXiv链接**: {arxiv_url}
- **代码链接**: (待补充)

**一句话概括**
{one_sentence}

**方法论**
{summary[:1000]}

**实验**
- 数据集: (待补充)
- 主要结果: (待补充)

**总结**
(待整理)

**后续改进**
(待分析)

---
*整理时间: {datetime.now().strftime('%Y-%m-%d')} | 分类: {category} | arXiv ID: {arxiv_id}*
"""
    return md


def save_paper(paper: dict, output_dir: str, category: str):
    """Save paper summary to file"""
    # Create year directory
    published = paper.get('published', '')
    year = published[:4] if published else str(extract_year_from_arxiv_id(paper.get('arxiv_id', '')))
    year_dir = os.path.join(output_dir, year, category)
    os.makedirs(year_dir, exist_ok=True)

    # Generate filename from title
    title = paper.get('title', 'unknown')
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = re.sub(r'\s+', '-', safe_title)[:50]
    filename = f"{safe_title}.md"

    # Handle duplicate filenames
    filepath = os.path.join(year_dir, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{safe_title}-{counter}.md"
        filepath = os.path.join(year_dir, filename)
        counter += 1

    # Generate and save content
    content = generate_paper_summary(paper, category)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Saved: {filepath}")
    return filepath


def main():
    """Main search function"""
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    config_path = script_dir / 'search_config.json'
    output_dir = script_dir / 'papers'

    print("=" * 60)
    print("Video CNN Interpretability Paper Search")
    print("=" * 60)

    # Load configuration
    config = load_config(config_path)
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

    # Save papers
    print("\n[保存论文]")
    saved_files = []
    for paper in unique_papers:
        category = paper.get('search_category', 'related')
        filepath = save_paper(paper, str(output_dir), category)
        saved_files.append(filepath)

    # Generate index
    print("\n[生成索引]")
    generate_index(output_dir, unique_papers)

    print(f"\n完成！已保存 {len(saved_files)} 篇论文到 {output_dir}")


def generate_index(output_dir: str, papers: list):
    """Generate index file with all papers"""
    # Group by year
    by_year = {}
    for paper in papers:
        published = paper.get('published', '')
        year = published[:4] if published else 'unknown'
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(paper)

    # Generate markdown
    index_md = "# 视频 CNN 可解释性论文索引\n\n"
    index_md += f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    index_md += f"总计: {len(papers)} 篇论文\n\n"

    # Sort years in descending order
    for year in sorted(by_year.keys(), reverse=True):
        index_md += f"## {year}\n\n"
        for paper in sorted(by_year[year], key=lambda x: x.get('title', '')):
            title = paper.get('title', 'Unknown')
            arxiv_url = paper.get('arxiv_url', '#')
            authors = paper.get('authors', [])[:3]
            authors_str = ', '.join(authors) + (' et al.' if len(authors) >= 3 else '')
            category = paper.get('search_category', 'related')

            index_md += f"- **[{title}]({arxiv_url})** - {authors_str} `[{category}]`\n"
        index_md += "\n"

    index_path = os.path.join(output_dir, '..', 'README.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_md)

    print(f"  Index saved to: {index_path}")


if __name__ == '__main__':
    main()
