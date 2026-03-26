# video-cnn-interpretability

📚 视频 CNN 可解释性相关论文自动搜索与整理

## 简介

这是一个自动化的论文搜索与整理系统，专注于视频理解、3D CNN、R(2+1)D 模型及相关可解释性研究。

## 搜索领域

### 核心领域
- R(2+1)D video classification interpretability
- 3D CNN video explainability
- Spatiotemporal convolution video understanding
- Video action recognition neural network

### 相关领域
- CNN interpretability explainability
- Network dissection deep vision
- Attention mechanism visualization
- Transformer video interpretability

## 项目结构

```
video-cnn-interpretability/
├── arxiv_search.py          # arXiv 搜索脚本
├── search_config.json       # 搜索配置文件
├── paper_template.md        # 论文总结模板
├── papers/
│   ├── 2017/
│   ├── 2018/
│   ├── ...
│   └── 2026/
│       ├── core/           # 核心领域论文
│       └── related/        # 相关领域论文
└── README.md               # 论文索引
```

## 使用方法

### 安装依赖

```bash
pip install arxiv
```

### 运行搜索

```bash
python arxiv_search.py
```

### 配置搜索关键词

编辑 `search_config.json` 来自定义搜索查询：

```json
{
  "search_queries": {
    "core": ["your core topic queries"],
    "related": ["your related topic queries"]
  },
  "max_results_per_query": 20
}
```

## 论文总结模板

每篇论文按以下格式整理：

- **基本信息**: 作者、发表、会议/期刊、arXiv链接、代码链接
- **一句话概括**: 论文核心贡献的简短描述
- **方法论**: 详细方法描述
- **实验**: 数据集和主要结果
- **总结**: 论文意义和局限性
- **后续改进**: 可能的改进方向

## 自动更新

可配合 cron/任务计划程序定期运行搜索脚本：

```bash
# 每周一早上9点运行
0 9 * * 1 python /path/to/arxiv_search.py
```

## 贡献

欢迎提交 Issue 或 Pull Request 来补充论文信息！

## 许可

本项目仅用于学术研究目的。
