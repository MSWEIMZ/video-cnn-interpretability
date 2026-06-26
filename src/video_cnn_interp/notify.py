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


def send_daily_digest(
    new_records: list[dict],
    stats: dict,
    errors: list[str] | None = None,
) -> bool:
    """发送每日摘要通知"""
    total = stats.get("total", 0)
    by_label = stats.get("by_label", {})
    core_new = [r for r in new_records if r.get("quality_label") == "core"]
    strong_new = [r for r in new_records if r.get("quality_label") == "strongly_related"]
    noise_blocked = stats.get("noise_blocked_today", 0)

    # 构建论文列表文本
    paper_lines: list[str] = []
    for p in core_new[:5]:
        paper_lines.append(f"🔥 {p.get('title', '')[:50]}")
    for p in strong_new[:3]:
        paper_lines.append(f"📎 {p.get('title', '')[:50]}")
    papers_text = "\n".join(paper_lines) if paper_lines else "今日无新增高质量论文"

    # 错误信息
    error_text = ""
    if errors:
        error_text = "\n⚠️ **异常**\n" + "\n".join(f"- {e}" for e in errors[:3])

    content = (
        f"📊 **论文库统计**\n"
        f"- 总计: {total} 篇\n"
        f"- 核心: {by_label.get('core', 0)} 篇\n"
        f"- 高相关: {by_label.get('strongly_related', 0)} 篇\n\n"
        f"📈 **今日新增** {len(new_records)} 篇\n"
        f"- 核心: {len(core_new)} 篇\n"
        f"- 高相关: {len(strong_new)} 篇\n"
        f"- 噪声拦截: {noise_blocked} 篇\n\n"
        f"📝 **重点论文**\n{papers_text}"
        f"{error_text}"
    )

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📚 论文日报 | 新增 {len(new_records)} 篇"},
                "template": "blue",
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
