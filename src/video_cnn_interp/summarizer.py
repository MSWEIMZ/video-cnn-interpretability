"""摘要增强模块 - 基于规则的一句话摘要与关联分析"""
from __future__ import annotations


# ---------- 扩展方法关键词表 ----------
METHOD_KEYWORDS: dict[str, list[str]] = {
    "gradient-based": ["grad-cam", "gradient", "backpropagation", "saliency map", "integrated gradient", "smoothgrad"],
    "attention-based": ["attention", "self-attention", "cross-attention", "transformer", "attention rollout", "attention map"],
    "perturbation-based": ["perturbation", "occlusion", "lime", "rise", "meaningful perturbation", "ablation"],
    "probing": ["probing", "probe", "linear classifier", "representation analysis", "feature visualization"],
    "concept-based": ["concept", "concept bottleneck", "network dissection", "tcav", "bottleneck"],
    "decomposition": ["decomposition", "tensor", "cp decomposition", "tucker", "r(2+1)d", "factored convolution"],
    "generative": ["generative", "generation", "diffusion", "gan", "vae", "synthesis", "reconstruction"],
    "benchmark": ["benchmark", "dataset", "evaluation", "survey", "review", "taxonomy", "comparison"],
    "visualization": ["visualization", "visualize", "feature map", "activation map", "heatmap", "cam"],
}


def _extract_first_sentences(text: str, max_chars: int = 200) -> str:
    """提取前 1-2 句话"""
    if not text:
        return ""
    sentences = text.replace("\n", " ").split(".")
    result = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if result:
            result += ". " + s
        else:
            result = s
        if len(result) >= max_chars:
            break
    return result.strip() + "." if result and not result.endswith(".") else result


def generate_one_line_summary(record: dict) -> str:
    """基于摘要生成一句话中文概述"""
    abstract = record.get("abstract", "")
    title = record.get("title", "")
    
    if not abstract:
        return title if title else "暂无摘要"
    
    # 提取核心方法和贡献
    first = _extract_first_sentences(abstract, 150)
    return first if first else abstract[:150] + "..."


def generate_summary_zh(record: dict) -> str:
    """生成一句话精炼摘要（≤80字），让人一眼知道这篇论文干什么。

    提取逻辑：
    1. 优先从 abstract 的第一句提取核心方法和贡献
    2. 如果第一句太短或太泛，取前两句
    3. 截断到 80 字以内，保持语句完整
    """
    abstract = record.get("abstract", "")
    title = record.get("title", "")

    if not abstract:
        return title[:80] if title else "暂无摘要"

    # 清理换行，按句号分句
    clean = abstract.replace("\n", " ").replace("\r", " ")
    sentences = [s.strip() for s in clean.split(".") if s.strip()]

    if not sentences:
        return abstract[:80]

    # 取第一句
    first = sentences[0]

    # 如果第一句太短（<30字）或太泛（只说了领域没说方法），加上第二句
    generic_starters = [
        "in this paper", "we propose", "we present", "we introduce",
        "recently", "deep learning", "neural network",
    ]
    first_lower = first.lower()
    is_generic = any(first_lower.startswith(g) for g in generic_starters) and len(first) < 60

    if is_generic and len(sentences) > 1:
        summary = first + ". " + sentences[1]
    elif len(first) < 30 and len(sentences) > 1:
        summary = first + ". " + sentences[1]
    else:
        summary = first

    # 截断到 80 字以内，不在单词中间截断
    if len(summary) > 80:
        summary = summary[:77]
        # 找最后一个空格截断，保持单词完整
        last_space = summary.rfind(" ")
        if last_space > 50:
            summary = summary[:last_space]
        summary += "..."

    return summary


def analyze_method_type(record: dict) -> str:
    """分析论文的方法类型（使用扩展关键词表）"""
    text = (record.get("title", "") + " " + record.get("abstract", "")).lower()
    
    matches = []
    for method, keywords in METHOD_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matches.append(method)
    
    return ", ".join(matches) if matches else "other"


def analyze_relation_to_r2plus1d(record: dict) -> str:
    """分析论文与 R(2+1)D / 视频 CNN 可解释性的关系"""
    text = (record.get("title", "") + " " + record.get("abstract", "")).lower()
    label = record.get("quality_label", "")
    
    # 直接相关
    r2plus1d_keywords = ["r(2+1)d", "r2plus1d", "r(2+1)D"]
    if any(kw in text for kw in r2plus1d_keywords):
        return "直接涉及 R(2+1)D 模型"
    
    # 3D CNN 相关
    cnn3d_keywords = ["3d cnn", "3d convolution", "spatiotemporal convolution", "c3d", "i3d"]
    if any(kw in text for kw in cnn3d_keywords):
        return "涉及 3D CNN / 时空卷积，与 R(2+1)D 方法论相关"
    
    # 视频可解释性
    video_interp = ["video", "action", "temporal"]
    interp = ["interpretab", "explainab", "saliency", "attention", "visualization", "attribution"]
    has_video = any(kw in text for kw in video_interp)
    has_interp = any(kw in text for kw in interp)
    
    if has_video and has_interp:
        return "视频可解释性相关研究，可参考其方法思路"
    if has_video:
        return "视频理解相关，但非直接聚焦可解释性"
    if has_interp:
        return "可解释性方法研究，可借鉴应用到视频 CNN"
    
    return "间接相关"


def detect_r2plus1d_mentions(record: dict) -> bool:
    """检测论文是否提及 R(2+1)D 或分解 3D 卷积相关概念"""
    text = (record.get("title", "") + " " + record.get("abstract", "")).lower()
    r2plus1d_terms = [
        "r(2+1)d", "r2plus1d", "r(2+1)D",
        "decomposed 3d convolution", "factored convolution",
        "decomposed 3d", "factored 3d",
    ]
    return any(term in text for term in r2plus1d_terms)


def _extract_r2plus1d_context(record: dict, window: int = 80) -> str:
    """提取 R(2+1)D 相关上下文片段"""
    abstract = record.get("abstract", "")
    text_lower = abstract.lower()
    terms = ["r(2+1)d", "r2plus1d", "decomposed 3d", "factored convolution"]
    for term in terms:
        idx = text_lower.find(term)
        if idx >= 0:
            start = max(0, idx - window)
            end = min(len(abstract), idx + len(term) + window)
            snippet = abstract[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(abstract):
                snippet = snippet + "..."
            return snippet
    return ""


def enhance_record(record: dict) -> dict:
    """为一条论文记录添加摘要增强字段"""
    record["one_line_summary"] = generate_one_line_summary(record)
    record["summary_zh"] = generate_summary_zh(record)
    record["method_type"] = analyze_method_type(record)
    record["relation_to_r2plus1d"] = analyze_relation_to_r2plus1d(record)

    # R(2+1)D 关系分析增强
    mentions_r2 = detect_r2plus1d_mentions(record)
    record["mentions_r2plus1d"] = mentions_r2
    if mentions_r2:
        record["r2plus1d_context"] = _extract_r2plus1d_context(record)
    else:
        record["r2plus1d_context"] = ""

    return record


def enhance_all_records(records: list[dict]) -> list[dict]:
    """批量增强所有记录"""
    return [enhance_record(r) for r in records]
