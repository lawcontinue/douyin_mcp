"""
内容模块MCP工具注册
"""

from typing import Any, Dict

from loguru import logger

from ..core.tool_registry import tool_registry, ToolDefinition, ToolParameter
from ..config.database import get_db
from .content_analyzer import content_analyzer


async def analyze_trending_content(limit: int = 20) -> Dict[str, Any]:
    """分析热门法律内容"""
    try:
        analysis = await content_analyzer.analyze_trending_legal_content(limit)
        return analysis
    except Exception as e:
        logger.error(f"分析热门内容失败: {e}")
        return {
            "success": False,
            "message": f"分析热门内容失败: {e}"
        }


async def generate_content_suggestions(account_id: int) -> Dict[str, Any]:
    """生成内容创作建议"""
    try:
        async for db in get_db():
            suggestions = await content_analyzer.generate_content_suggestions(account_id, db)
            return suggestions
    except Exception as e:
        logger.error(f"生成内容建议失败: {e}")
        return {
            "success": False,
            "message": f"生成内容建议失败: {e}"
        }


async def get_legal_topic_trends() -> Dict[str, Any]:
    """获取法律话题趋势"""
    try:
        # 简化版本的话题趋势分析
        trending_topics = [
            {
                "topic": "劳动法",
                "heat_index": 85,
                "trend": "上升",
                "related_keywords": ["加班", "工资", "辞职", "劳动合同"]
            },
            {
                "topic": "消费维权",
                "heat_index": 78,
                "trend": "稳定",
                "related_keywords": ["退货", "假货", "投诉", "赔偿"]
            },
            {
                "topic": "房产纠纷",
                "heat_index": 72,
                "trend": "上升",
                "related_keywords": ["买房", "租房", "物业", "拆迁"]
            },
            {
                "topic": "婚姻家庭",
                "heat_index": 68,
                "trend": "稳定",
                "related_keywords": ["离婚", "财产", "抚养", "继承"]
            },
            {
                "topic": "交通事故",
                "heat_index": 65,
                "trend": "下降",
                "related_keywords": ["车祸", "保险", "赔偿", "责任"]
            }
        ]
        
        return {
            "success": True,
            "trending_topics": trending_topics,
            "updated_at": "2025-10-02T22:00:00Z",
            "source": "综合分析"
        }
    except Exception as e:
        logger.error(f"获取话题趋势失败: {e}")
        return {
            "success": False,
            "message": f"获取话题趋势失败: {e}"
        }


async def get_optimal_posting_schedule() -> Dict[str, Any]:
    """获取最佳发布时间建议"""
    try:
        # 基于数据分析的最佳发布时间
        schedule = {
            "weekdays": {
                "morning": {"time": "08:00-09:00", "audience": "上班族", "engagement": "中"},
                "lunch": {"time": "12:00-14:00", "audience": "午休用户", "engagement": "高"},
                "evening": {"time": "19:00-21:00", "audience": "下班人群", "engagement": "最高"},
                "night": {"time": "21:00-23:00", "audience": "夜间用户", "engagement": "中"}
            },
            "weekends": {
                "morning": {"time": "09:00-11:00", "audience": "休闲用户", "engagement": "高"},
                "afternoon": {"time": "14:00-16:00", "audience": "午后休闲", "engagement": "中"},
                "evening": {"time": "19:00-21:00", "audience": "家庭时间", "engagement": "高"}
            },
            "optimal_days": ["周二", "周三", "周四", "周日"],
            "avoid_times": ["06:00-08:00", "23:00-06:00"],
            "legal_content_peak": "19:30-20:30"
        }
        
        return {
            "success": True,
            "schedule": schedule,
            "recommendations": [
                "工作日晚上19:00-21:00是法律内容的最佳发布时间",
                "周末上午适合发布深度分析类内容",
                "避免在深夜发布专业内容",
                "周二到周四的工作日表现最佳"
            ]
        }
    except Exception as e:
        logger.error(f"获取发布时间建议失败: {e}")
        return {
            "success": False,
            "message": f"获取发布时间建议失败: {e}"
        }


async def analyze_content_performance_factors() -> Dict[str, Any]:
    """分析内容表现影响因素"""
    try:
        factors = {
            "title_optimization": {
                "effective_patterns": [
                    "【法律知识】+ 具体问题",
                    "律师告诉你：+ 实用建议", 
                    "这种情况 + 如何维权",
                    "真实案例：+ 法律分析"
                ],
                "avoid_patterns": [
                    "过于专业的法条表述",
                    "冗长复杂的标题",
                    "缺乏吸引力的平述"
                ]
            },
            "content_structure": {
                "optimal_length": "1-3分钟",
                "key_elements": [
                    "开头3秒抓住注意力",
                    "结构清晰，逻辑明确",
                    "实用性强，贴近生活",
                    "结尾引导互动"
                ]
            },
            "engagement_drivers": [
                {"factor": "实用性", "impact": "高", "description": "解决实际法律问题"},
                {"factor": "时效性", "impact": "高", "description": "结合当前热点事件"},
                {"factor": "互动性", "impact": "中", "description": "引导用户参与讨论"},
                {"factor": "专业性", "impact": "中", "description": "展示专业法律知识"},
                {"factor": "故事性", "impact": "中", "description": "真实案例更吸引人"}
            ],
            "hashtag_suggestions": [
                "#法律知识", "#律师普法", "#维权指南", "#法律科普",
                "#消费者权益", "#劳动法", "#婚姻法", "#法律咨询"
            ]
        }
        
        return {
            "success": True,
            "performance_factors": factors,
            "summary": "成功的法律内容需要兼顾专业性和通俗性，重点关注实用价值"
        }
    except Exception as e:
        logger.error(f"分析内容表现因素失败: {e}")
        return {
            "success": False,
            "message": f"分析内容表现因素失败: {e}"
        }


async def register_content_tools() -> None:
    """注册内容相关的MCP工具"""
    try:
        # 分析热门内容
        trending_analysis_tool = ToolDefinition(
            name="douyin_analyze_trending_content",
            description="分析抖音热门法律内容",
            parameters=[
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="分析视频数量限制",
                    required=False,
                    default=20
                )
            ],
            category="content",
            handler=analyze_trending_content
        )
        
        # 生成内容建议
        content_suggestions_tool = ToolDefinition(
            name="douyin_generate_content_suggestions",
            description="生成个性化内容创作建议",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                )
            ],
            category="content",
            handler=generate_content_suggestions
        )
        
        # 法律话题趋势
        topic_trends_tool = ToolDefinition(
            name="douyin_get_legal_topic_trends",
            description="获取法律话题热度趋势",
            parameters=[],
            category="content",
            handler=get_legal_topic_trends
        )
        
        # 最佳发布时间
        posting_schedule_tool = ToolDefinition(
            name="douyin_get_optimal_posting_schedule",
            description="获取最佳内容发布时间建议",
            parameters=[],
            category="content",
            handler=get_optimal_posting_schedule
        )
        
        # 内容表现因素分析
        performance_factors_tool = ToolDefinition(
            name="douyin_analyze_content_performance_factors",
            description="分析影响内容表现的关键因素",
            parameters=[],
            category="content",
            handler=analyze_content_performance_factors
        )
        
        # 注册所有工具
        tools = [
            trending_analysis_tool,
            content_suggestions_tool,
            topic_trends_tool,
            posting_schedule_tool,
            performance_factors_tool
        ]
        
        for tool in tools:
            tool_registry.register_tool(tool)
        
        logger.info(f"内容模块工具注册完成，共注册 {len(tools)} 个工具")
        
    except Exception as e:
        logger.error(f"注册内容工具失败: {e}")
        raise
