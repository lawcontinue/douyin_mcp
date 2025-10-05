"""
分析模块MCP工具注册
"""

from typing import Any, Dict

from loguru import logger

from ..core.tool_registry import tool_registry, ToolDefinition, ToolParameter
from ..config.database import get_db
from .analytics_engine import analytics_engine


async def get_account_overview(account_id: int, days: int = 30) -> Dict[str, Any]:
    """获取账号概览数据"""
    try:
        async for db in get_db():
            overview = await analytics_engine.get_account_overview(account_id, db, days)
            return {
                "success": True,
                "data": overview
            }
    except Exception as e:
        logger.error(f"获取账号概览失败: {e}")
        return {
            "success": False,
            "message": f"获取账号概览失败: {e}"
        }


async def get_engagement_trends(account_id: int, days: int = 30) -> Dict[str, Any]:
    """获取互动趋势数据"""
    try:
        async for db in get_db():
            trends = await analytics_engine.get_engagement_trends(account_id, db, days)
            return trends
    except Exception as e:
        logger.error(f"获取互动趋势失败: {e}")
        return {
            "success": False,
            "message": f"获取互动趋势失败: {e}"
        }


async def get_comment_analysis(account_id: int, days: int = 30) -> Dict[str, Any]:
    """获取评论分析数据"""
    try:
        async for db in get_db():
            analysis = await analytics_engine.get_comment_categories_analysis(account_id, db, days)
            return analysis
    except Exception as e:
        logger.error(f"获取评论分析失败: {e}")
        return {
            "success": False,
            "message": f"获取评论分析失败: {e}"
        }


async def get_template_performance(account_id: int) -> Dict[str, Any]:
    """获取模板效果分析"""
    try:
        async for db in get_db():
            performance = await analytics_engine.get_template_performance(account_id, db)
            return performance
    except Exception as e:
        logger.error(f"获取模板效果分析失败: {e}")
        return {
            "success": False,
            "message": f"获取模板效果分析失败: {e}"
        }


async def get_conversion_analysis(account_id: int, days: int = 30) -> Dict[str, Any]:
    """获取转化分析数据"""
    try:
        async for db in get_db():
            analysis = await analytics_engine.get_conversion_analysis(account_id, db, days)
            return analysis
    except Exception as e:
        logger.error(f"获取转化分析失败: {e}")
        return {
            "success": False,
            "message": f"获取转化分析失败: {e}"
        }


async def generate_comprehensive_report(account_id: int, days: int = 30) -> Dict[str, Any]:
    """生成综合分析报告"""
    try:
        async for db in get_db():
            report = await analytics_engine.generate_comprehensive_report(account_id, db, days)
            return report
    except Exception as e:
        logger.error(f"生成综合报告失败: {e}")
        return {
            "success": False,
            "message": f"生成综合报告失败: {e}"
        }


async def register_analytics_tools() -> None:
    """注册分析相关的MCP工具"""
    try:
        # 账号概览
        overview_tool = ToolDefinition(
            name="douyin_get_account_overview",
            description="获取抖音账号数据概览",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="统计天数",
                    required=False,
                    default=30
                )
            ],
            category="analytics",
            handler=get_account_overview
        )
        
        # 互动趋势
        trends_tool = ToolDefinition(
            name="douyin_get_engagement_trends",
            description="获取互动趋势数据",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="统计天数",
                    required=False,
                    default=30
                )
            ],
            category="analytics",
            handler=get_engagement_trends
        )
        
        # 评论分析
        comment_analysis_tool = ToolDefinition(
            name="douyin_get_comment_analysis",
            description="获取评论分类分析数据",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="统计天数",
                    required=False,
                    default=30
                )
            ],
            category="analytics",
            handler=get_comment_analysis
        )
        
        # 模板效果
        template_performance_tool = ToolDefinition(
            name="douyin_get_template_performance",
            description="获取回复模板效果分析",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                )
            ],
            category="analytics",
            handler=get_template_performance
        )
        
        # 转化分析
        conversion_tool = ToolDefinition(
            name="douyin_get_conversion_analysis",
            description="获取转化效果分析",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="统计天数",
                    required=False,
                    default=30
                )
            ],
            category="analytics",
            handler=get_conversion_analysis
        )
        
        # 综合报告
        report_tool = ToolDefinition(
            name="douyin_generate_report",
            description="生成综合分析报告",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="统计天数",
                    required=False,
                    default=30
                )
            ],
            category="analytics",
            handler=generate_comprehensive_report
        )
        
        # 注册所有工具
        tools = [
            overview_tool,
            trends_tool,
            comment_analysis_tool,
            template_performance_tool,
            conversion_tool,
            report_tool
        ]
        
        for tool in tools:
            tool_registry.register_tool(tool)
        
        logger.info(f"分析模块工具注册完成，共注册 {len(tools)} 个工具")
        
    except Exception as e:
        logger.error(f"注册分析工具失败: {e}")
        raise
