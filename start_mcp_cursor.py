#!/usr/bin/env python3
"""
MCP服务器启动脚本 - 专为Cursor配置
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def register_all_tools():
    """注册所有工具"""
    print("正在注册工具...")
    
    from src.auth.tools import register_auth_tools
    await register_auth_tools()
    print("认证工具注册成功")
    
    from src.monitor.tools import register_monitor_tools
    await register_monitor_tools()
    print("监控工具注册成功")
    
    from src.reply.tools import register_reply_tools
    await register_reply_tools()
    print("回复工具注册成功")
    
    from src.analytics.tools import register_analytics_tools
    await register_analytics_tools()
    print("分析工具注册成功")
    
    from src.content.tools import register_content_tools
    await register_content_tools()
    print("内容工具注册成功")
    
    from src.core.tool_registry import tool_registry
    print(f"总共注册了 {len(tool_registry.tools)} 个工具")

def main():
    """主函数"""
    from src.config.settings import settings
    from src.config.database import db_config
    from src.core.mcp_server import mcp_server
    import uvicorn
    
    print("正在启动MCP服务器...")
    print(f"服务器地址: http://{settings.API_HOST}:{settings.API_PORT}")
    
    # 初始化数据库
    db_config.initialize()
    
    # 注册所有工具
    asyncio.run(register_all_tools())
    
    # 启动服务器
    uvicorn.run(
        mcp_server.app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()

