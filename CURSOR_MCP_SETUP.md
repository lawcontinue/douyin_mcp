# 🚀 Cursor MCP 配置指南

## 📋 配置步骤

### 1. 找到Cursor的MCP配置文件

Cursor的MCP配置文件通常位于以下位置：

**Windows:**
```
%APPDATA%\Cursor\User\globalStorage\cursor.mcp\config.json
```

**macOS:**
```
~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/config.json
```

**Linux:**
```
~/.config/Cursor/User/globalStorage/cursor.mcp/config.json
```

### 2. 配置MCP服务器

将以下配置添加到Cursor的MCP配置文件中：

```json
{
  "mcpServers": {
    "douyin-lawyer-mcp": {
      "command": "python",
      "args": ["start_mcp_cursor.py"],
      "cwd": "D:\\cloud\\findlawwanted\\douyin-comment-mcp",
      "env": {
        "PYTHONPATH": "D:\\cloud\\findlawwanted\\douyin-comment-mcp",
        "API_PORT": "8002"
      }
    }
  }
}
```

### 3. 完整的配置文件示例

如果你的Cursor MCP配置文件已经存在其他配置，请将上面的配置合并到现有的 `mcpServers` 对象中：

```json
{
  "mcpServers": {
    "existing-server": {
      // 你现有的MCP服务器配置
    },
    "douyin-lawyer-mcp": {
      "command": "python",
      "args": ["start_mcp_cursor.py"],
      "cwd": "D:\\cloud\\findlawwanted\\douyin-comment-mcp",
      "env": {
        "PYTHONPATH": "D:\\cloud\\findlawwanted\\douyin-comment-mcp",
        "API_PORT": "8002"
      }
    }
  }
}
```

## 🔧 配置说明

### 参数解释

- **`command`**: 启动命令，使用Python
- **`args`**: 启动参数，指向我们的MCP启动脚本
- **`cwd`**: 工作目录，设置为项目根目录
- **`env`**: 环境变量
  - `PYTHONPATH`: 确保Python能找到项目模块
  - `API_PORT`: 设置服务器端口为8001

### 路径配置

**重要**: 请根据你的实际项目路径修改 `cwd` 参数：

- 当前配置: `"D:\\cloud\\findlawwanted\\douyin-comment-mcp"`
- 请替换为你的实际项目路径

## 🚀 启动和测试

### 1. 手动测试MCP服务器

在配置Cursor之前，你可以先手动测试MCP服务器：

```bash
cd D:\cloud\findlawwanted\douyin-comment-mcp
python start_mcp_cursor.py
```

### 2. 验证服务器运行

打开浏览器访问：
- 健康检查: http://localhost:8002/health
- API文档: http://localhost:8002/docs
- 工具列表: http://localhost:8002/tools

### 3. 重启Cursor

配置完成后，重启Cursor以加载新的MCP配置。

## 🎯 可用的MCP工具

配置成功后，你可以在Cursor中使用以下33个工具：

### 认证模块 (8个工具)
- `douyin_login` - 抖音登录
- `douyin_create_account` - 创建账号
- `douyin_list_accounts` - 账号列表
- `douyin_update_account` - 更新账号
- `douyin_delete_account` - 删除账号
- `douyin_logout` - 登出
- `douyin_validate_session` - 验证会话
- `douyin_account_stats` - 账号统计

### 监控模块 (6个工具)
- `douyin_create_monitor_task` - 创建监控任务
- `douyin_start_monitor_task` - 启动监控任务
- `douyin_stop_monitor_task` - 停止监控任务
- `douyin_list_monitor_tasks` - 监控任务列表
- `douyin_get_monitor_task_stats` - 监控任务统计
- `douyin_get_recent_comments` - 获取最近评论

### 回复模块 (8个工具)
- `douyin_create_reply_template` - 创建回复模板
- `douyin_generate_ai_reply` - AI生成回复
- `douyin_send_reply` - 发送回复
- `douyin_auto_reply_comments` - 自动回复评论
- `douyin_process_pending_replies` - 处理待回复
- `douyin_get_reply_templates` - 获取回复模板
- `douyin_get_reply_stats` - 回复统计
- `douyin_get_recent_replies` - 获取最近回复

### 分析模块 (6个工具)
- `douyin_get_account_overview` - 账号概览
- `douyin_get_engagement_trends` - 互动趋势
- `douyin_get_comment_analysis` - 评论分析
- `douyin_get_template_performance` - 模板性能
- `douyin_get_conversion_analysis` - 转化分析
- `douyin_generate_report` - 生成报告

### 内容模块 (5个工具)
- `douyin_analyze_trending_content` - 分析热门内容
- `douyin_generate_content_suggestions` - 生成内容建议
- `douyin_get_legal_topic_trends` - 法律话题趋势
- `douyin_get_optimal_posting_schedule` - 最佳发布时间
- `douyin_analyze_content_performance_factors` - 内容性能分析

## 🔍 使用示例

配置完成后，你可以在Cursor中直接使用这些工具，例如：

```
请帮我创建一个抖音监控任务，监控关键词"法律咨询"
```

或者：

```
请帮我分析最近的评论数据并生成报告
```

## 🛠️ 故障排除

### 1. 端口冲突

如果遇到端口冲突，可以修改 `API_PORT` 环境变量：

```json
"env": {
  "PYTHONPATH": "D:\\cloud\\findlawwanted\\douyin-comment-mcp",
  "API_PORT": "8002"
}
```

### 2. 路径问题

确保 `cwd` 路径正确，使用绝对路径：

```json
"cwd": "D:\\cloud\\findlawwanted\\douyin-comment-mcp"
```

### 3. Python环境

确保Cursor使用的Python环境包含所有必要的依赖包。

### 4. 权限问题

确保Cursor有权限访问项目目录和启动Python脚本。

## 📞 支持

如果遇到问题，请检查：

1. MCP服务器是否正常启动
2. 端口是否被占用
3. 项目路径是否正确
4. Python环境是否配置正确

---

*配置完成后，你就可以在Cursor中直接使用抖音自动回复评论监测工具的所有功能了！*

