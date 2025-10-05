#!/usr/bin/env python3
"""
测试服务器启动
"""
import sys
from pathlib import Path
import uvicorn

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def register_all_tools():
    """注册所有工具"""
    print("正在注册工具...")
    
    try:
        # 注册认证工具
        from src.auth.tools import register_auth_tools
        await register_auth_tools()
        print("认证工具注册成功")
        
        # 注册其他工具
        try:
            from src.monitor.tools import register_monitor_tools
            await register_monitor_tools()
            print("监控工具注册成功")
        except Exception as e:
            print(f"监控工具注册失败: {e}")
        
        try:
            from src.reply.tools import register_reply_tools
            await register_reply_tools()
            print("回复工具注册成功")
        except Exception as e:
            print(f"回复工具注册失败: {e}")
        
        try:
            from src.analytics.tools import register_analytics_tools
            await register_analytics_tools()
            print("分析工具注册成功")
        except Exception as e:
            print(f"分析工具注册失败: {e}")
        
        try:
            from src.content.tools import register_content_tools
            await register_content_tools()
            print("内容工具注册成功")
        except Exception as e:
            print(f"内容工具注册失败: {e}")
        
        # 显示注册的工具数量
        from src.core.tool_registry import tool_registry
        print(f"总共注册了 {len(tool_registry.tools)} 个工具")
        
    except Exception as e:
        print(f"工具注册失败: {e}")

def main():
    """主函数"""
    print("正在测试服务器启动...")
    
    try:
        # 导入配置
        from src.config.settings import settings
        print(f"配置加载成功 - 环境: {settings.ENVIRONMENT}")
        
        # 初始化数据库
        from src.config.database import db_config
        print("初始化数据库...")
        db_config.initialize()
        
        # 导入MCP服务器
        from src.core.mcp_server import mcp_server
        print(f"MCP服务器加载成功 - {mcp_server.name}")
        
        # 注册工具
        import asyncio
        asyncio.run(register_all_tools())
        
        # 直接启动服务器
        print(f"启动服务器在 {settings.API_HOST}:{settings.API_PORT}")
        
        uvicorn.run(
            mcp_server.app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level="info",
            reload=False
        )
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
