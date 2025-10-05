"""
主程序入口
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.mcp_server import mcp_server
from src.config.settings import settings
from src.config.database import db_config
from src.config.redis_config import redis_config

# 初始化控制台
console = Console()
app = typer.Typer(
    name="douyin-mcp",
    help="抖音律师MCP工具",
    add_completion=False
)


def setup_logging() -> None:
    """配置日志"""
    # 移除默认日志处理器
    logger.remove()
    
    # 控制台日志
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 文件日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 错误日志
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )


async def initialize_services() -> None:
    """初始化服务"""
    console.print("🚀 初始化服务...")
    
    try:
        # 初始化数据库
        console.print("📊 初始化数据库连接...")
        db_config.initialize()
        await db_config.create_tables()
        console.print("✅ 数据库初始化完成")
        
        # 初始化Redis
        if settings.ENABLE_REDIS_CACHE:
            console.print("🔄 初始化Redis连接...")
            redis_config.initialize()
            if await redis_config.ping():
                console.print("✅ Redis连接成功")
            else:
                console.print("⚠️ Redis连接失败，将使用内存缓存")
        
        # 注册工具
        console.print("🔧 注册MCP工具...")
        await register_tools()
        console.print("✅ 工具注册完成")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        console.print(f"❌ 服务初始化失败: {e}")
        raise


async def register_tools() -> None:
    """注册所有MCP工具"""
    from src.auth.tools import register_auth_tools
    from src.monitor.tools import register_monitor_tools
    from src.reply.tools import register_reply_tools
    from src.analytics.tools import register_analytics_tools
    from src.content.tools import register_content_tools
    
    # 注册各模块工具
    await register_auth_tools()
    await register_monitor_tools()
    await register_reply_tools()
    await register_analytics_tools()
    await register_content_tools()


async def cleanup_services() -> None:
    """清理服务"""
    console.print("🧹 清理服务...")
    
    try:
        # 关闭数据库连接
        await db_config.close()
        
        # 关闭Redis连接
        if settings.ENABLE_REDIS_CACHE:
            await redis_config.close()
        
        console.print("✅ 服务清理完成")
        
    except Exception as e:
        logger.error(f"服务清理失败: {e}")
        console.print(f"⚠️ 服务清理失败: {e}")


@app.command()
def start(
    host: str = typer.Option(settings.API_HOST, "--host", "-h", help="服务器主机地址"),
    port: int = typer.Option(settings.API_PORT, "--port", "-p", help="服务器端口"),
    reload: bool = typer.Option(settings.DEBUG, "--reload", "-r", help="开启热重载"),
    workers: Optional[int] = typer.Option(None, "--workers", "-w", help="工作进程数量")
) -> None:
    """启动MCP服务器"""
    
    # 显示启动信息
    title = Text("抖音律师MCP工具", style="bold blue")
    subtitle = Text(f"v{mcp_server.version}", style="dim")
    info_panel = Panel(
        f"{title}\n{subtitle}\n\n"
        f"🌐 服务地址: http://{host}:{port}\n"
        f"📚 API文档: http://{host}:{port}/docs\n"
        f"🔧 环境模式: {settings.ENVIRONMENT}\n"
        f"📝 日志级别: {settings.LOG_LEVEL}",
        title="[bold green]启动信息[/bold green]",
        border_style="green"
    )
    console.print(info_panel)
    
    async def run_server():
        try:
            await initialize_services()
            
            # 启动参数
            run_kwargs = {
                "host": host,
                "port": port,
                "reload": reload,
                "access_log": settings.DEBUG
            }
            
            if workers and workers > 1:
                run_kwargs["workers"] = workers
            
            # 启动服务器
            await mcp_server.start(**run_kwargs)
            
        except KeyboardInterrupt:
            console.print("\n⚠️ 收到中断信号，正在关闭服务...")
        except Exception as e:
            logger.error(f"服务器运行失败: {e}")
            console.print(f"❌ 服务器运行失败: {e}")
        finally:
            await cleanup_services()
    
    # 运行服务器
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        console.print("\n👋 服务已停止")


@app.command()
def version() -> None:
    """显示版本信息"""
    console.print(f"抖音律师MCP工具 v{mcp_server.version}")


@app.command()
def config() -> None:
    """显示当前配置"""
    config_info = f"""
🔧 配置信息:
├── 环境: {settings.ENVIRONMENT}
├── 调试模式: {settings.DEBUG}
├── 日志级别: {settings.LOG_LEVEL}
├── API地址: {settings.API_HOST}:{settings.API_PORT}
├── 数据库: {'已配置' if settings.DATABASE_URL else '未配置'}
├── Redis: {'已启用' if settings.ENABLE_REDIS_CACHE else '已禁用'}
├── 自动回复: {'已启用' if settings.ENABLE_AUTO_REPLY else '已禁用'}
├── 监控间隔: {settings.MONITOR_INTERVAL}秒
└── 每小时最大回复数: {settings.MAX_REPLIES_PER_HOUR}
"""
    
    config_panel = Panel(
        config_info.strip(),
        title="[bold cyan]当前配置[/bold cyan]",
        border_style="cyan"
    )
    console.print(config_panel)


@app.command()
def check() -> None:
    """检查环境和依赖"""
    
    async def run_checks():
        console.print("🔍 检查环境和依赖...\n")
        
        checks = []
        
        # 检查Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append(("Python版本", python_version, ">=3.9"))
        
        # 检查数据库连接
        try:
            db_config.initialize()
            checks.append(("数据库连接", "✅ 正常", ""))
        except Exception as e:
            checks.append(("数据库连接", f"❌ 失败: {e}", ""))
        
        # 检查Redis连接
        if settings.ENABLE_REDIS_CACHE:
            try:
                redis_config.initialize()
                if await redis_config.ping():
                    checks.append(("Redis连接", "✅ 正常", ""))
                else:
                    checks.append(("Redis连接", "❌ 失败", ""))
            except Exception as e:
                checks.append(("Redis连接", f"❌ 失败: {e}", ""))
        else:
            checks.append(("Redis连接", "⚠️ 已禁用", ""))
        
        # 检查API密钥
        if settings.OPENAI_API_KEY:
            checks.append(("OpenAI API", "✅ 已配置", ""))
        else:
            checks.append(("OpenAI API", "⚠️ 未配置", ""))
        
        if settings.ANTHROPIC_API_KEY:
            checks.append(("Anthropic API", "✅ 已配置", ""))
        else:
            checks.append(("Anthropic API", "⚠️ 未配置", ""))
        
        # 显示检查结果
        for name, status, requirement in checks:
            if requirement:
                console.print(f"📋 {name}: {status} ({requirement})")
            else:
                console.print(f"📋 {name}: {status}")
        
        await cleanup_services()
    
    asyncio.run(run_checks())


def main() -> None:
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 运行CLI应用
    app()


if __name__ == "__main__":
    main()
