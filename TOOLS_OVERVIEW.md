# 抖音律师MCP工具总览

本文档提供所有可用MCP工具的完整列表和使用说明。

## 🔧 工具分类

### 认证管理 (auth)
管理抖音账号的登录、认证和会话。

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `douyin_login` | 登录抖音账号 | username, login_type, password, qr_uuid |
| `douyin_create_account` | 创建账号记录 | username, login_type, password, phone_number |
| `douyin_list_accounts` | 获取账号列表 | limit, offset |
| `douyin_update_account` | 更新账号信息 | account_id, nickname, enable_monitoring |
| `douyin_delete_account` | 删除账号 | account_id |
| `douyin_logout` | 登出账号 | session_token |
| `douyin_validate_session` | 验证会话 | session_token |
| `douyin_account_stats` | 获取账号统计 | - |

### 监测引擎 (monitor)
监测视频评论、私信和@提及。

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `douyin_create_monitor_task` | 创建监测任务 | account_id, task_name, keywords, check_interval |
| `douyin_start_monitor_task` | 启动监测任务 | task_id |
| `douyin_stop_monitor_task` | 停止监测任务 | task_id |
| `douyin_list_monitor_tasks` | 获取监测任务列表 | account_id |
| `douyin_get_monitor_task_stats` | 获取任务统计 | task_id |
| `douyin_get_recent_comments` | 获取最近评论 | task_id, limit, category |

### 智能回复 (reply)
AI驱动的智能回复系统。

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `douyin_create_reply_template` | 创建回复模板 | account_id, template_name, category, content |
| `douyin_generate_ai_reply` | 生成AI回复 | comment_content, reply_style, max_length |
| `douyin_send_reply` | 发送回复 | comment_id, account_id, reply_content |
| `douyin_auto_reply_comments` | 自动回复评论 | account_id, limit |
| `douyin_process_pending_replies` | 处理待发送回复 | limit |
| `douyin_get_reply_templates` | 获取回复模板 | account_id, category |
| `douyin_get_reply_stats` | 获取回复统计 | account_id, days |
| `douyin_get_recent_replies` | 获取回复记录 | account_id, limit, status |

### 数据分析 (analytics)
全面的数据统计和分析报告。

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `douyin_get_account_overview` | 获取账号概览 | account_id, days |
| `douyin_get_engagement_trends` | 获取互动趋势 | account_id, days |
| `douyin_get_comment_analysis` | 获取评论分析 | account_id, days |
| `douyin_get_template_performance` | 获取模板效果 | account_id |
| `douyin_get_conversion_analysis` | 获取转化分析 | account_id, days |
| `douyin_generate_report` | 生成综合报告 | account_id, days |

### 内容分析 (content)
热门内容分析和创作建议。

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `douyin_analyze_trending_content` | 分析热门内容 | limit |
| `douyin_generate_content_suggestions` | 生成创作建议 | account_id |
| `douyin_get_legal_topic_trends` | 获取话题趋势 | - |
| `douyin_get_optimal_posting_schedule` | 获取发布时间建议 | - |
| `douyin_analyze_content_performance_factors` | 分析内容表现因素 | - |

## 🚀 快速开始

### 1. 账号登录
```python
# 二维码登录
result = await tool_registry.execute_tool("douyin_login", {
    "username": "your_username",
    "login_type": "qrcode"
})

# 密码登录
result = await tool_registry.execute_tool("douyin_login", {
    "username": "your_username", 
    "login_type": "password",
    "password": "your_password"
})
```

### 2. 创建监测任务
```python
result = await tool_registry.execute_tool("douyin_create_monitor_task", {
    "account_id": 1,
    "task_name": "法律咨询监测",
    "keywords": ["法律咨询", "律师", "维权"],
    "check_interval": 300
})
```

### 3. 生成AI回复
```python
result = await tool_registry.execute_tool("douyin_generate_ai_reply", {
    "comment_content": "这种情况该怎么维权？",
    "reply_style": "professional",
    "include_call_to_action": True
})
```

### 4. 获取数据分析
```python
result = await tool_registry.execute_tool("douyin_generate_report", {
    "account_id": 1,
    "days": 30
})
```

## 📋 使用场景

### 场景1：新账号设置
1. `douyin_create_account` - 创建账号记录
2. `douyin_login` - 登录账号
3. `douyin_create_monitor_task` - 创建监测任务
4. `douyin_create_reply_template` - 创建回复模板

### 场景2：日常运营
1. `douyin_get_recent_comments` - 查看新评论
2. `douyin_auto_reply_comments` - 自动回复
3. `douyin_process_pending_replies` - 处理待发送回复
4. `douyin_get_reply_stats` - 查看回复效果

### 场景3：数据分析
1. `douyin_get_account_overview` - 查看账号概览
2. `douyin_get_engagement_trends` - 分析互动趋势
3. `douyin_generate_report` - 生成综合报告
4. `douyin_analyze_trending_content` - 分析热门内容

### 场景4：内容优化
1. `douyin_get_legal_topic_trends` - 了解热门话题
2. `douyin_generate_content_suggestions` - 获取创作建议
3. `douyin_get_optimal_posting_schedule` - 优化发布时间
4. `douyin_analyze_content_performance_factors` - 分析成功因素

## ⚠️ 注意事项

### 频率限制
- 监测任务最小间隔：60秒
- 自动回复每小时限制：默认10条
- API调用建议间隔：2-5秒

### 数据安全
- 所有敏感数据加密存储
- 会话令牌定期更新
- 支持HTTPS通信

### 最佳实践
1. **登录管理**：使用二维码登录更安全可靠
2. **监测配置**：合理设置关键词和检查频率
3. **回复策略**：结合模板和AI生成获得最佳效果
4. **数据分析**：定期查看报告调整策略
5. **内容创作**：基于趋势分析制定内容计划

## 🔍 错误处理

### 常见错误类型
- `AUTH_ERROR`：认证相关错误
- `MONITOR_ERROR`：监测相关错误
- `REPLY_ERROR`：回复相关错误
- `RATE_LIMIT_ERROR`：频率限制错误

### 错误处理建议
```python
result = await tool_registry.execute_tool("tool_name", parameters)

if not result.get("success"):
    error = result.get("error", {})
    error_code = error.get("error_code")
    
    if error_code == "RATE_LIMIT_ERROR":
        # 等待并重试
        retry_after = error.get("details", {}).get("retry_after", 60)
        await asyncio.sleep(retry_after)
    elif error_code == "AUTH_ERROR":
        # 重新登录
        await re_login()
    else:
        # 其他错误处理
        logger.error(f"工具执行失败: {error}")
```

## 📚 扩展功能

### 自定义回复策略
可以通过回复规则和模板系统实现复杂的回复逻辑：

1. 创建多个模板覆盖不同场景
2. 设置关键词触发条件
3. 配置情感分析规则
4. 定义优先级和时间限制

### 数据导出
支持多种格式的数据导出：
- CSV格式的统计数据
- JSON格式的详细记录
- Excel格式的分析报告

### 第三方集成
- Webhook通知
- 邮件报告
- 数据同步接口
- 监控告警系统

---

📖 更多详细信息请参考 [API文档](http://localhost:8000/docs) 和 [README.md](README.md)。
