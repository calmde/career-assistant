# 参与贡献

感谢你对四步求职助手项目的关注！欢迎提交 Issue、PR 和改进建议。

## 行为准则

- 保持友善和尊重
- 欢迎不同观点
- 聚焦在"如何提升项目质量"

## 如何贡献

### 报告 Bug

1. 确保你在使用最新的 `main` 分支
2. 搜索已有 [Issues](../../issues) 避免重复
3. 提交 Issue 并包含：
   - **环境信息**：Python 版本、操作系统、浏览器版本
   - **复现步骤**：详细描述触发 Bug 的操作
   - **期望行为 vs 实际行为**
   - **错误日志**（如果有）

### 提新功能

1. 先开 Issue 讨论需求 → 避免浪费精力
2. 描述功能的价值和使用场景

### 提交代码

1. **Fork** 本仓库
2. 从 `main` 创建特性分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 遵循现有代码风格：
   - 使用 4 空格缩进
   - 函数和类添加 docstring
   - 变量和函数名使用 `snake_case`
   - 注释用中文
4. 确保改动通过现有测试（如果有）：
   ```bash
   python -m pytest tests/
   ```
5. 提交 PR 时填写变更说明

### PR 审核标准

- 代码清晰、可读
- 不引入新的安全风险（硬编码密钥、SQL 注入等）
- 新功能有对应的文档说明
- 向后兼容（除非有充分理由破坏）

## 项目结构速览

```
├── app.py                  # Flask Web 入口
├── job_parser.py           # 岗位/简历解析器
├── matcher.py              # 多维匹配引擎
├── resume_optimizer.py     # 简历优化
├── skill_navigator.py      # 技能规划
├── pipeline.py             # 流程编排（CLI）
├── spider.py               # BOSS直聘爬虫
├── clean_data.py           # 数据清洗入库
├── seed_data.py            # 种子数据
├── llm_client.py           # LLM API 客户端
├── scrapers/               # 第三方抓取器
├── utils/                  # 工具函数
├── templates/              # Jinja2 模板
├── tests/                  # 测试
└── docs/                   # 设计文档
```

## 本地开发

```bash
# 克隆
git clone https://github.com/calmde/career-assistant.git
cd career-assistant

# 安装依赖
pip install -r requirements.txt

# 初始化数据
python seed_data.py

# 启动（开发模式）
FLASK_DEBUG=1 python app.py

# 运行测试
python -m pytest tests/
```

## 环境变量

参考 [`.env.example`](.env.example)：

| 变量 | 说明 | 必填 |
|------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | 否（不填则纯本地模式） |
| `LLM_API_BASE` | API 地址 | 否 |
| `LLM_MODEL` | 模型名 | 否 |
| `FLASK_SECRET_KEY` | Flask 密钥 | 否（自动生成） |
| `FLASK_DEBUG` | 调试模式 | 否 |

---

再次感谢！🎉
