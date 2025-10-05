# 抖音律师MCP工具

一个专为律师设计的抖音自动评论监测与智能回复系统，基于Model Context Protocol (MCP)构建，帮助律师高效管理抖音互动、打造个人IP并精准获客。

## 🚀 核心功能

### 📱 账号管理
- 多账号支持，独立配置管理
- 多种登录方式：扫码/短信/密码
- 智能会话保持与自动续期
- 账号状态实时监控

### 🔍 智能监测
- 实时评论监测
- 私信消息监控
- @提及自动检测
- 关键词触发机制
- 智能频率控制

### 🤖 AI智能回复
- 内容智能分类（法律咨询、感谢、质疑等）
- 多层次回复策略
- 个性化回复生成
- 智能导流优化
- 上下文理解

### 📊 数据分析
- 全面互动数据统计
- 回复效果分析
- 转化率跟踪
- 可视化报告生成
- 竞品对比分析

### 📈 内容分析
- 热门法律话题追踪
- 创作建议生成
- 最佳发布时间分析
- 选题推荐系统

## 🛠️ 技术架构

```
后端框架：FastAPI + uvicorn
异步处理：asyncio + celery + redis
数据存储：PostgreSQL + Redis缓存
爬虫引擎：Playwright + 代理池
AI集成：OpenAI API + Anthropic Claude
监控告警：Prometheus + Grafana
```

## 📁 项目结构

```
douyin-lawyer-mcp/
├── src/
│   ├── core/                 # 核心MCP服务
│   ├── auth/                 # 账号管理
│   ├── monitor/              # 监测引擎
│   ├── reply/                # 智能回复
│   ├── analytics/            # 数据分析
│   ├── content/              # 内容分析
│   ├── config/               # 配置管理
│   └── utils/                # 工具函数
├── data/
│   ├── templates/            # 回复模板
│   ├── cache/                # 缓存数据
│   └── exports/              # 导出文件
├── tests/                    # 测试文件
├── docs/                     # 文档
├── docker/                   # 容器配置
└── scripts/                  # 脚本工具
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (用于Playwright)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/lawyer-mcp/douyin-comment-mcp.git
cd douyin-comment-mcp
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置信息
```

5. **初始化数据库**
```bash
python scripts/init_db.py
```

6. **启动服务**
```bash
python -m src.core.main
```

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 📋 使用指南

### 1. 账号配置
```python
# 添加抖音账号
await auth_manager.add_account(
    username="your_username",
    login_type="qrcode"
)
```

### 2. 设置监测规则
```python
# 配置监测规则
monitor_config = {
    "keywords": ["法律咨询", "维权", "律师"],
    "video_types": ["普法", "案例分析"],
    "priority": "high"
}
```

### 3. 自定义回复模板
```python
# 法律咨询类回复模板
templates = {
    "legal_consultation": [
        "感谢您的咨询！这是一个很专业的法律问题，建议私信详细沟通 📝",
        "您提到的情况确实需要仔细分析，欢迎私信获取专业建议 ⚖️"
    ]
}
```

## 🔧 高级配置

### AI模型配置
支持多种AI模型集成：
- OpenAI GPT-4/GPT-3.5
- Anthropic Claude
- 本地化模型部署

### 监控与告警
- Prometheus指标监控
- Grafana可视化面板
- 邮件/webhook通知

### 安全与合规
- 内容合规检查
- 风险预警系统
- 操作审计日志

## 📊 功能特色

### 🎯 律师专业化
- 法律领域专业术语识别
- 案例推荐系统
- 法律风险评估
- 专业形象维护

### 🚀 智能化程度高
- 情感分析
- 用户画像
- 个性化回复
- 学习优化

### 📈 营销导流
- 精准用户识别
- 转化路径优化
- A/B测试支持
- ROI跟踪分析

## 🔒 安全特性

- 账号安全防护
- 数据加密存储
- API访问控制
- 操作日志审计
- 风险行为检测

## 📚 API文档

启动服务后访问 `http://localhost:8000/docs` 查看完整的API文档。

### 主要接口

- `POST /auth/login` - 账号登录
- `GET /monitor/status` - 监测状态
- `POST /reply/auto` - 自动回复
- `GET /analytics/report` - 数据报告
- `POST /content/analyze` - 内容分析

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=src tests/
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- 📧 邮箱: support@lawyer-mcp.com
- 💬 微信群: [扫码加入]
- 🐛 Bug报告: [GitHub Issues](https://github.com/lawyer-mcp/douyin-comment-mcp/issues)
- 📖 文档: [在线文档](https://docs.lawyer-mcp.com)

## 🙏 致谢

感谢所有贡献者和以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)
- [OpenAI](https://openai.com/)
- [Anthropic](https://www.anthropic.com/)

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
