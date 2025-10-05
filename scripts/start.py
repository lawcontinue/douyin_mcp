#!/usr/bin/env python3
"""
启动脚本 - 便捷启动抖音律师MCP工具
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    print("🚀 启动抖音律师MCP工具")
    
    # 检查虚拟环境
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  建议在虚拟环境中运行")
    
    # 检查环境文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 未找到.env文件，请先复制.env.example并配置")
        sys.exit(1)
    
    # 启动服务
    try:
        os.chdir(project_root)
        cmd = [sys.executable, "-m", "src.core.main", "start"]
        
        # 传递命令行参数
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
