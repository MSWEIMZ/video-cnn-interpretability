"""飞书通知模块"""
from __future__ import annotations
import json
import os
from urllib.request import urlopen, Request


def _get_webhook() -> str:
    """获取飞书 webhook URL"""
    return os.environ.get("FEISHU_WEBHOOK", "")


def _send_feishu_card(card: dict) -> bool:
    """发送飞书卡片消息"""
    webhook = _get_webhook()
    if not webhook:
        print("  [INFO] 未配置 FEISHU_WEBHOOK，跳过通知")
        return False
    try:
        data = json.dumps(card, ensure_ascii=False).encode("utf-8")
        req = Request(webhook, data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                return True
            print(f"  [WARN] 飞书返回: {result}")
            return False
    except Exception as e:
        print(f"  [WARN] 飞书通知失败: {e}")
        return False


def _format_paper_line(p: dict, icon: str) -> str:
    """格式化单篇论文为通知行，包含链接、引用量、作者"""
    title = p.get("title", "")[:50]
    url = p.get("url", "")
    authors = p.get("authors", [])
    author_str = ", ".join(authors[:2])
    if len(authors) > 2:
        author_str += " et al."
    citation = p.get("citation_count", 0)
    venue = p.get("venue", "")

    parts = [f"{icon} "]
    if url:
        parts.append(f"[{title}]({url})")
    else:
        parts.append(title)

    details = []
    if author_str:
        details.append(author_str)
    if venue:
        details.append(venue)
    if citation > 0:
        details.append(f"引用 {citation}")

    if details:
        parts.append(f" ({', '.join(details)})")

    return "".join(parts)


def _build_daily_content(new_records: list[dict], stats: dict, errors: list[str] | None = None) -> str:
    """构建有新增论文时的通知内容"""
    total = stats.get("total", 0)
    by_label = stats.get("by_label", {})
    noise_blocked = stats.get("noise_blocked_today", 0)

    core_new = [r for r in new_records if r.get("quality_label") == "core"]
    strong_new = [r for r in new_records if r.get("quality_label") == "strongly_related"]

    # 论文列表
    paper_lines: list[str] = []
    for p in core_new[:5]:
        paper_lines.append(_format_paper_line(p, "🔥"))
    for p in strong_new[:3]:
        paper_lines.append(_format_paper_line(p, "📎"))
    papers_text = "\n".join(paper_lines)

    # 错误信息
    error_text = ""
    if errors:
        error_text = "\n\n⚠️ **异常**\n" + "\n".join(f"- {e}" for e in errors[:3])

    content = (
        f"📊 **论文库统计**\n"
        f"- 总计: {total} 篇 | 核心: {by_label.get('core', 0)} | 高相关: {by_label.get('strongly_related', 0)}\n\n"
        f"📈 **今日新增** {len(new_records)} 篇 "
        f"(核心 {len(core_new)} | 高相关 {len(strong_new)} | 噪声拦截 {noise_blocked})\n\n"
        f"📝 **重点论文**\n{papers_text}"
        f"{error_text}"
    )
    return content


def _build_no_new_content(stats: dict) -> str:
    """构建无新增论文时的简短通知内容"""
    total = stats.get("total", 0)
    by_label = stats.get("by_label", {})
    return (
        f"📊 **论文库统计**\n"
        f"- 总计: {total} 篇 | 核心: {by_label.get('core', 0)} | 高相关: {by_label.get('strongly_related', 0)}\n\n"
        f"ℹ️ 今日无新增论文"
    )


def send_daily_digest(
    new_records: list[dict],
    stats: dict,
    errors: list[str] | None = None,
) -> bool:
    """发送每日摘要通知"""
    if not new_records:
        content = _build_no_new_content(stats)
        header_title = "📚 论文日报 | 无新增"
        template = "grey"
    else:
        content = _build_daily_content(new_records, stats, errors)
        header_title = f"📚 论文日报 | 新增 {len(new_records)} 篇"
        template = "blue"

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": template,
            },
            "elements": [
                {"tag": "markdown", "content": content},
            ],
        },
    }
    return _send_feishu_card(card)


def send_error_alert(error_msg: str) -> bool:
    """发送错误告警"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🚨 论文搜索异常"},
                "template": "red",
            },
            "elements": [
                {"tag": "markdown", "content": f"**错误信息**\n{error_msg[:500]}"},
            ],
        },
    }
    return _send_feishu_card(card)
