#!/usr/bin/env python3
"""
直接启动MCP服务器
"""
import sys
from pathlib import Path
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """主函数"""
    print("正在启动抖音律师MCP工具服务器...")
    
    try:
        # 导入必要模块
        from src.config.settings import settings
        from src.config.database import db_config
        from src.core.mcp_server import mcp_server
        from src.auth.tools import register_auth_tools
        
        print(f"环境: {settings.ENVIRONMENT}")
        print(f"API地址: {settings.API_HOST}:{settings.API_PORT}")
        
        # 初始化数据库
        print("初始化数据库...")
        db_config.initialize()
        await db_config.create_tables()
        
        # 注册工具
        print("注册工具...")
        await register_auth_tools()
        
        # 启动服务器
        print("启动Web服务器...")
        mcp_server.run(
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG
        )
        
    except KeyboardInterrupt:
        print("服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

