#!/usr/bin/env python3
"""
MCP服务器启动脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 创建必要的目录
data_dir = project_root / "data"
logs_dir = project_root / "logs"
data_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)

try:
    # 测试导入
    print("正在测试导入...")
    from src.config.settings import settings
    print("✅ 配置模块导入成功")
    
    # 测试基础组件
    from src.core.mcp_server import mcp_server
    print("✅ MCP服务器模块导入成功")
    
    # 打印配置信息
    print(f"🔧 环境: {settings.ENVIRONMENT}")
    print(f"🔧 调试模式: {settings.DEBUG}")
    print(f"🔧 API地址: {settings.API_HOST}:{settings.API_PORT}")
    
    print("\n🚀 正在启动MCP服务器...")
    
    # 启动服务器
    import uvicorn
    uvicorn.run(
        "src.core.mcp_server:mcp_server.app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保安装了所有依赖。尝试运行: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ 启动失败: {e}")
    print("请检查配置文件和环境设置")
