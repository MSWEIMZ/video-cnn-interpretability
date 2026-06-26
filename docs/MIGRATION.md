# 迁移说明：v1 -> v2

## 概述

本次改造将 `video-cnn-interpretability` 从单一的 arXiv 搜索脚本升级为模块化的论文情报系统。

## 主要变化

### 架构变化

| v1 | v2 |
|----|----|
| 单一 `arxiv_search.py` | `src/video_cnn_interp/` 模块化包 |
| 直接写 Markdown 文件 | JSONL 索引 + Markdown 卡片 |
| 无评分过滤 | 关键词加权 + 类别加分 + 黑名单过滤 |
| `search_queries` 配置 | `queries` 配置（三层查询） |
| `git add -A` | 白名单提交 |

### 新模块

- `config.py`：配置加载与校验
- `collector.py`：arXiv 搜索收集
- `normalizer.py`：论文数据规范化
- `scorer.py`：相关性评分与质量标签
- `storage.py`：JSONL 索引存储
- `readme.py`：README / ALL_PAPERS 生成
- `notify.py`：飞书通知
- `cli.py`：统一 CLI 入口

### 数据变化

- 新增 `papers/index.jsonl`：主索引，每行一条论文记录
- 新增 `ALL_PAPERS.md`：完整论文列表
- `README.md` 改为精选视图 + 年份折叠

### 配置变化

旧配置 `search_config.json` 使用 `search_queries.core` / `search_queries.related`。

新配置使用：
- `queries.core`：核心查询
- `queries.expanded`：扩展查询
- `queries.exploratory`：探索查询
- `filters`：年份、类别、黑名单、主题关键词
- `scoring`：评分阈值与权重
- `runtime`：运行时配置

## 如何运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行每日搜索
PYTHONPATH=src python -m video_cnn_interp.cli run-daily
```

## 旧脚本兼容

`arxiv_search.py` 仍保留，但不再推荐使用。主流程已迁移到 `cli.py`。

## GitHub Actions

`.github/workflows/arxiv_search.yml` 已更新为使用新入口。
