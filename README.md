# 📚 视频 CNN 可解释性论文库

> 自动化论文搜索与整理系统 | 专注于 3DCNN、R(2+1)D 模型及可解释性研究

## 📊 统计概览

- **论文总数**: 待更新
- **核心论文**: 待更新
- **高相关论文**: 待更新
- **最后更新**: 待更新

---

## 🔥 最新核心论文

*首次运行后自动生成*

## 📎 高相关论文

*首次运行后自动生成*

---

## ⚙️ 自动更新

本项目通过 **GitHub Actions** 每天自动搜索 arXiv 最新论文，经评分筛选后入库。

### 运行方式

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m video_cnn_interp.cli run-daily
```

### 架构

```
src/video_cnn_interp/
├── config.py        # 配置加载
├── collector.py     # arXiv 搜索
├── normalizer.py    # 数据规范化
├── scorer.py        # 评分与标签
├── storage.py       # JSONL 索引
├── readme.py        # README 生成
├── notify.py        # 飞书通知
└── cli.py           # CLI 入口
```

## 📄 License

仅供学术研究使用
