"""主题聚类模块"""
from __future__ import annotations
from collections import defaultdict


# 主题定义：每个主题包含一组关键词（命中 title/abstract 任一即算命中）
TOPIC_DEFINITIONS: dict[str, dict] = {
    "temporal_explanation": {
        "name": "Temporal Explanation",
        "name_cn": "时序解释",
        "keywords": ["temporal", "time", "sequence", "frame", "shuffling"],
        "description": "聚焦于视频时序维度的可解释性研究",
    },
    "video_saliency": {
        "name": "Video Saliency",
        "name_cn": "视频显著性",
        "keywords": ["saliency", "salienc", "attention map", "grad-cam", "gradcam", "heatmap", "spatial attention"],
        "description": "视频/空间显著性检测与可视化",
    },
    "attention_attribution": {
        "name": "Attention & Attribution",
        "name_cn": "注意力与归因",
        "keywords": ["attention mechanism", "attribution", "gradient", "backprop", "integrated gradient", "lime", "shap"],
        "description": "注意力机制分析与梯度归因方法",
    },
    "3d_cnn_explanation": {
        "name": "3D CNN Explanation",
        "name_cn": "3D CNN 解释",
        "keywords": ["3D CNN", "3D convolution", "spatiotemporal convolution", "R(2+1)D", "r(2+1)d", "decomposed 3d", "C3D", "I3D"],
        "description": "3D 卷积网络 / R(2+1)D 等时空卷积模型的可解释性",
    },
    "action_recognition_interpretability": {
        "name": "Action Recognition Interpretability",
        "name_cn": "动作识别可解释性",
        "keywords": ["action recognition", "action classification", "video classification", "video understanding"],
        "description": "视频动作识别 / 分类任务的可解释性研究",
    },
    "network_dissection": {
        "name": "Network Dissection",
        "name_cn": "网络解剖",
        "keywords": ["network dissection", "unit visualization", "feature visualization", "neuron", "representation"],
        "description": "网络内部单元 / 特征可视化与解剖",
    },
    "video_transformer": {
        "name": "Video Transformer Interpretability",
        "name_cn": "视频 Transformer 可解释性",
        "keywords": ["transformer", "vit", "self-attention", "multi-head", "video transformer"],
        "description": "Vision Transformer / Video Transformer 的可解释性",
    },
    "robustness_adversarial": {
        "name": "Robustness & Adversarial",
        "name_cn": "鲁棒性与对抗",
        "keywords": ["robustness", "adversarial", "defense", "attack", "perturbation"],
        "description": "视频模型的鲁棒性与对抗攻击/防御",
    },
}


def classify_paper_topics(record: dict) -> list[str]:
    """将一篇论文归入一个或多个主题，返回主题 ID 列表"""
    title = record.get("title", "").lower()
    abstract = record.get("abstract", "").lower()
    combined = f"{title} {abstract}"
    
    matched = []
    for topic_id, topic_def in TOPIC_DEFINITIONS.items():
        keywords = topic_def["keywords"]
        if any(kw.lower() in combined for kw in keywords):
            matched.append(topic_id)
    return matched


def cluster_papers_by_topic(records: list[dict]) -> dict[str, list[dict]]:
    """将所有论文按主题聚类，返回 {topic_id: [records]} """
    clusters: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        topics = classify_paper_topics(rec)
        for t in topics:
            clusters[t].append(rec)
        if not topics:
            clusters["uncategorized"].append(rec)
    # 每个主题内按分数降序
    for t in clusters:
        clusters[t].sort(key=lambda r: -r.get("relevance_score", 0))
    return dict(clusters)


def get_topic_stats(records: list[dict]) -> list[dict]:
    """返回主题统计信息，按论文数降序排列"""
    clusters = cluster_papers_by_topic(records)
    stats = []
    for topic_id, papers in clusters.items():
        if topic_id == "uncategorized":
            continue
        topic_def = TOPIC_DEFINITIONS.get(topic_id, {})
        core_count = sum(1 for p in papers if p.get("quality_label") == "core")
        stats.append({
            "topic_id": topic_id,
            "name": topic_def.get("name", topic_id),
            "name_cn": topic_def.get("name_cn", topic_id),
            "description": topic_def.get("description", ""),
            "total": len(papers),
            "core_count": core_count,
            "top_papers": papers[:5],
        })
    stats.sort(key=lambda s: -s["total"])
    return stats


def generate_topics_markdown(records: list[dict]) -> str:
    """生成主题视图 Markdown"""
    topic_stats = get_topic_stats(records)
    clusters = cluster_papers_by_topic(records)
    
    lines: list[str] = []
    lines.append("# 📂 主题视图")
    lines.append("")
    lines.append(f"> 共 {len(topic_stats)} 个主题 | 最后更新: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 📊 主题概览")
    lines.append("")
    lines.append("| 主题 | 论文数 | 核心论文 | 说明 |")
    lines.append("|------|--------|----------|------|")
    for s in topic_stats:
        lines.append(f"| {s['name_cn']} | {s['total']} | {s['core_count']} | {s['description']} |")
    
    uncategorized = clusters.get("uncategorized", [])
    if uncategorized:
        lines.append(f"| 未分类 | {len(uncategorized)} | - | - |")
    lines.append("")
    
    # 每个主题的详情
    for s in topic_stats:
        topic_id = s["topic_id"]
        papers = clusters.get(topic_id, [])
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## {s['name_cn']} ({s['name']})")
        lines.append(f"")
        lines.append(f"> {s['description']}")
        lines.append(f"")
        if papers:
            lines.append("| 标签 | 标题 | 年份 | 分数 |")
            lines.append("|------|------|------|------|")
            icon_map = {"core": "🔥", "strongly_related": "📎", "weakly_related": "📝"}
            for p in papers[:15]:
                icon = icon_map.get(p.get("quality_label", ""), "📝")
                title = p.get("title", "")[:60]
                year = p.get("year", "")
                score = p.get("relevance_score", 0)
                url = p.get("url", "#")
                lines.append(f"| {icon} | [{title}]({url}) | {year} | {score} |")
            if len(papers) > 15:
                lines.append(f"")
                lines.append(f"*... 共 {len(papers)} 篇，仅显示前 15 篇*")
        else:
            lines.append("*暂无论文*")
        lines.append("")
    
    return "\n".join(lines)
