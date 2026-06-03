<p align="center">
  <h1 align="center">🎓 四步求职助手</h1>
  <p align="center"><strong>一站式智能求职工具：爬取岗位 → 匹配评估 → 简历优化 → 技能规划</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 📖 简介

四步求职助手是一个面向**大学毕业生**的全流程求职工具，围绕求职的四个关键步骤构建：

```
上传简历 ──→ ① 岗位解析 ──→ ② 匹配评估 ──→ ③ 简历优化 ──→ ④ 技能规划
```

| 步骤 | 功能 | 技术方案 |
|------|------|----------|
| **① 岗位解析** | 爬取招聘网站岗位 + 手动粘贴JD，结构化提取技能/学历/经验要求 | jieba分词 + 200+技能词表 + 正则规则 |
| **② 匹配评估** | 简历与岗位多维打分（技能40% + 经验20% + 学历20% + 类别10% + 行业10%） | 本地规则评分 + LLM语义复核（可选） |
| **③ 简历优化** | 关键词布局建议、项目量化改写、ATS友好度检测 | LLM API（DeepSeek / OpenAI 兼容） |
| **④ 技能规划** | 缺失技能分级、学习路径推荐、替代岗位建议 | LLM API + 本地课程模板库 |

### 核心特点

- 🧠 **混合智能**：本地规则处理核心匹配，LLM 处理语义理解和内容生成
- 🛡️ **可降级运行**：LLM API 不可用时，系统自动降级为纯本地模式，核心功能不受影响
- 🌐 **Flask Web 界面**：美观的网页交互，上传简历、浏览岗位、查看匹配报告一站式
- 🕷️ **多源爬虫**：支持 V2EX、jobspy 等多渠道岗位抓取
- 📊 **种子数据**：内置 35 条覆盖 Python/Java/前端/算法/测试/产品的示例岗位，爬虫失效时仍可完整体验

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- （可选）Chrome 浏览器 — 用于 Selenium 爬虫

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/career-assistant.git
cd career-assistant

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env，填入你的 API Key（可选，不填则使用纯本地模式）
# LLM_API_KEY=your-api-key-here
# LLM_API_BASE=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-chat
```

### 初始化种子数据

```bash
python seed_data.py
```

### 启动

```bash
python app.py
```

浏览器打开 `http://127.0.0.1:5000` 即可使用。

---

## 📁 项目结构

```
├── app.py                  # Flask Web 应用主入口
├── job_parser.py           # 岗位描述解析器（结构化提取）
├── matcher.py              # 匹配引擎（多维度打分 + LLM复核）
├── resume_optimizer.py     # 简历优化器（LLM 改写建议）
├── skill_navigator.py      # 技能导航（学习路径 + 替代岗位）
├── pipeline.py             # 流程编排器（批量处理）
├── spider.py               # 爬虫调度
├── clean_data.py           # 数据清洗
├── seed_data.py            # 种子数据生成（35条示例岗位）
├── llm_client.py           # LLM API 客户端（OpenAI 兼容）
├── analyze_match.py        # 匹配分析辅助
├── scrapers/
│   └── integrations.py     # 第三方爬虫（V2EX / jobspy）
├── utils/
│   └── anti_scrape.py      # 反反爬工具
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础布局
│   ├── index.html          # 首页（上传简历）
│   ├── jobs.html           # 岗位浏览
│   ├── match.html          # 匹配详情
│   ├── optimize.html       # 简历优化
│   └── skill_plan.html     # 技能计划
├── tests/                  # 测试文件
├── docs/                   # 设计文档
├── requirements.txt        # Python 依赖
└── .env.example            # 环境变量模板
```

---

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | Flask 3.0 |
| 数据库 | SQLite（可迁移至 PostgreSQL） |
| 爬虫 | requests + BeautifulSoup + Selenium + DrissionPage + jobspy |
| NLP | jieba 分词 + 自定义词表 |
| LLM | OpenAI 兼容接口（DeepSeek / 通义千问 / 本地模型） |
| 前端 | Jinja2 模板 + 原生 CSS |

---

## 🧪 运行测试

```bash
python -m pytest tests/
```

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

## ⚠️ 免责声明

本工具仅供学习和技术研究使用。使用爬虫功能抓取招聘网站数据时，请遵守目标网站的 robots.txt 和服务条款，合理控制抓取频率，勿用于商业用途。由此产生的任何法律风险由使用者自行承担。
