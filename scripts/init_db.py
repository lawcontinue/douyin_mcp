#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.database import db_config
from src.config.settings import settings
from loguru import logger

async def init_database():
    """初始化数据库"""
    try:
        print("初始化数据库...")
        
        # 初始化数据库连接
        db_config.initialize()
        
        # 创建所有表
        await db_config.create_tables()
        
        print("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("抖音律师MCP工具 - 数据库初始化")
    print(f"数据库URL: {settings.DATABASE_URL[:50]}...")
    
    # 运行初始化
    asyncio.run(init_database())

if __name__ == "__main__":
    main()
