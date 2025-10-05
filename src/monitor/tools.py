"""
监测模块MCP工具注册
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from ..core.tool_registry import tool_registry, ToolDefinition, ToolParameter
from ..config.database import get_db
from .monitor_engine import monitor_engine
from .models import MonitorTaskCreate, MonitorTaskUpdate, MonitorStatus


async def create_monitor_task(
    account_id: int,
    task_name: str,
    description: Optional[str] = None,
    monitor_videos: bool = True,
    monitor_comments: bool = True,
    monitor_messages: bool = True,
    monitor_mentions: bool = True,
    keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
    check_interval: int = 300,
    max_videos_per_check: int = 10,
    min_comment_length: int = 5,
    max_comment_length: int = 500,
    filter_spam: bool = True
) -> Dict[str, Any]:
    """创建监测任务"""
    try:
        async for db in get_db():
            task_data = MonitorTaskCreate(
                account_id=account_id,
                task_name=task_name,
                description=description,
                monitor_videos=monitor_videos,
                monitor_comments=monitor_comments,
                monitor_messages=monitor_messages,
                monitor_mentions=monitor_mentions,
                keywords=keywords,
                exclude_keywords=exclude_keywords,
                check_interval=check_interval,
                max_videos_per_check=max_videos_per_check,
                min_comment_length=min_comment_length,
                max_comment_length=max_comment_length,
                filter_spam=filter_spam
            )
            
            task = await monitor_engine.create_monitor_task(task_data, db)
            
            return {
                "success": True,
                "message": "监测任务创建成功",
                "task": {
                    "id": task.id,
                    "task_name": task.task_name,
                    "account_id": task.account_id,
                    "status": task.status,
                    "check_interval": task.check_interval,
                    "created_at": task.created_at.isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"创建监测任务失败: {e}")
        return {
            "success": False,
            "message": f"创建监测任务失败: {e}"
        }


async def start_monitor_task(task_id: int) -> Dict[str, Any]:
    """启动监测任务"""
    try:
        async for db in get_db():
            success = await monitor_engine.start_monitor_task(task_id, db)
            
            if success:
                return {
                    "success": True,
                    "message": f"监测任务 {task_id} 启动成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"监测任务 {task_id} 启动失败"
                }
                
    except Exception as e:
        logger.error(f"启动监测任务失败: {e}")
        return {
            "success": False,
            "message": f"启动监测任务失败: {e}"
        }


async def stop_monitor_task(task_id: int) -> Dict[str, Any]:
    """停止监测任务"""
    try:
        async for db in get_db():
            success = await monitor_engine.stop_monitor_task(task_id, db)
            
            if success:
                return {
                    "success": True,
                    "message": f"监测任务 {task_id} 停止成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"监测任务 {task_id} 停止失败"
                }
                
    except Exception as e:
        logger.error(f"停止监测任务失败: {e}")
        return {
            "success": False,
            "message": f"停止监测任务失败: {e}"
        }


async def list_monitor_tasks(account_id: Optional[int] = None) -> Dict[str, Any]:
    """获取监测任务列表"""
    try:
        async for db in get_db():
            tasks = await monitor_engine.list_monitor_tasks(db, account_id)
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "id": task.id,
                    "account_id": task.account_id,
                    "task_name": task.task_name,
                    "description": task.description,
                    "status": task.status,
                    "monitor_videos": task.monitor_videos,
                    "monitor_comments": task.monitor_comments,
                    "monitor_messages": task.monitor_messages,
                    "monitor_mentions": task.monitor_mentions,
                    "keywords": task.keywords,
                    "check_interval": task.check_interval,
                    "total_videos_monitored": task.total_videos_monitored,
                    "total_comments_found": task.total_comments_found,
                    "total_replies_sent": task.total_replies_sent,
                    "created_at": task.created_at.isoformat(),
                    "last_check_at": task.last_check_at.isoformat() if task.last_check_at else None,
                    "next_check_at": task.next_check_at.isoformat() if task.next_check_at else None
                })
            
            return {
                "success": True,
                "tasks": task_list,
                "total": len(task_list)
            }
            
    except Exception as e:
        logger.error(f"获取监测任务列表失败: {e}")
        return {
            "success": False,
            "message": f"获取监测任务列表失败: {e}",
            "tasks": []
        }


async def get_monitor_task_stats(task_id: int) -> Dict[str, Any]:
    """获取监测任务统计信息"""
    try:
        async for db in get_db():
            stats = await monitor_engine.get_task_statistics(task_id, db)
            
            if stats:
                return {
                    "success": True,
                    "statistics": stats
                }
            else:
                return {
                    "success": False,
                    "message": f"监测任务 {task_id} 不存在"
                }
                
    except Exception as e:
        logger.error(f"获取监测任务统计失败: {e}")
        return {
            "success": False,
            "message": f"获取监测任务统计失败: {e}"
        }


async def get_recent_comments(
    task_id: Optional[int] = None,
    limit: int = 50,
    category: Optional[str] = None,
    is_processed: Optional[bool] = None
) -> Dict[str, Any]:
    """获取最近的评论数据"""
    try:
        async for db in get_db():
            from sqlalchemy import select, and_
            from .models import CommentData
            
            # 构建查询
            query = select(CommentData).order_by(CommentData.created_at.desc()).limit(limit)
            
            conditions = []
            if task_id:
                conditions.append(CommentData.monitor_task_id == task_id)
            if category:
                conditions.append(CommentData.category == category)
            if is_processed is not None:
                conditions.append(CommentData.is_processed == is_processed)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await db.execute(query)
            comments = result.scalars().all()
            
            comment_list = []
            for comment in comments:
                comment_list.append({
                    "id": comment.id,
                    "comment_id": comment.comment_id,
                    "content": comment.content,
                    "author_name": comment.author_name,
                    "category": comment.category,
                    "keywords_matched": comment.keywords_matched,
                    "sentiment": comment.sentiment,
                    "is_processed": comment.is_processed,
                    "is_replied": comment.is_replied,
                    "reply_content": comment.reply_content,
                    "like_count": comment.like_count,
                    "quality_score": comment.quality_score,
                    "is_spam": comment.is_spam,
                    "comment_time": comment.comment_time.isoformat() if comment.comment_time else None,
                    "created_at": comment.created_at.isoformat()
                })
            
            return {
                "success": True,
                "comments": comment_list,
                "total": len(comment_list)
            }
            
    except Exception as e:
        logger.error(f"获取评论数据失败: {e}")
        return {
            "success": False,
            "message": f"获取评论数据失败: {e}",
            "comments": []
        }


async def register_monitor_tools() -> None:
    """注册监测相关的MCP工具"""
    try:
        # 创建监测任务
        create_task_tool = ToolDefinition(
            name="douyin_create_monitor_task",
            description="创建抖音监测任务",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="task_name",
                    type="string",
                    description="任务名称",
                    required=True
                ),
                ToolParameter(
                    name="description",
                    type="string",
                    description="任务描述",
                    required=False
                ),
                ToolParameter(
                    name="monitor_videos",
                    type="boolean",
                    description="监测视频",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="monitor_comments",
                    type="boolean",
                    description="监测评论",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="monitor_messages",
                    type="boolean",
                    description="监测私信",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="monitor_mentions",
                    type="boolean",
                    description="监测@提及",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="keywords",
                    type="array",
                    description="监测关键词列表",
                    required=False
                ),
                ToolParameter(
                    name="exclude_keywords",
                    type="array",
                    description="排除关键词列表",
                    required=False
                ),
                ToolParameter(
                    name="check_interval",
                    type="integer",
                    description="检查间隔（秒）",
                    required=False,
                    default=300
                ),
                ToolParameter(
                    name="max_videos_per_check",
                    type="integer",
                    description="每次检查最大视频数",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="filter_spam",
                    type="boolean",
                    description="过滤垃圾评论",
                    required=False,
                    default=True
                )
            ],
            category="monitor",
            handler=create_monitor_task
        )
        
        # 启动监测任务
        start_task_tool = ToolDefinition(
            name="douyin_start_monitor_task",
            description="启动抖音监测任务",
            parameters=[
                ToolParameter(
                    name="task_id",
                    type="integer",
                    description="任务ID",
                    required=True
                )
            ],
            category="monitor",
            handler=start_monitor_task
        )
        
        # 停止监测任务
        stop_task_tool = ToolDefinition(
            name="douyin_stop_monitor_task",
            description="停止抖音监测任务",
            parameters=[
                ToolParameter(
                    name="task_id",
                    type="integer",
                    description="任务ID",
                    required=True
                )
            ],
            category="monitor",
            handler=stop_monitor_task
        )
        
        # 获取监测任务列表
        list_tasks_tool = ToolDefinition(
            name="douyin_list_monitor_tasks",
            description="获取抖音监测任务列表",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID（可选，过滤指定账号的任务）",
                    required=False
                )
            ],
            category="monitor",
            handler=list_monitor_tasks
        )
        
        # 获取任务统计
        task_stats_tool = ToolDefinition(
            name="douyin_get_monitor_task_stats",
            description="获取监测任务统计信息",
            parameters=[
                ToolParameter(
                    name="task_id",
                    type="integer",
                    description="任务ID",
                    required=True
                )
            ],
            category="monitor",
            handler=get_monitor_task_stats
        )
        
        # 获取最近评论
        recent_comments_tool = ToolDefinition(
            name="douyin_get_recent_comments",
            description="获取最近的评论数据",
            parameters=[
                ToolParameter(
                    name="task_id",
                    type="integer",
                    description="任务ID（可选）",
                    required=False
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="返回数量限制",
                    required=False,
                    default=50
                ),
                ToolParameter(
                    name="category",
                    type="string",
                    description="评论分类过滤",
                    required=False
                ),
                ToolParameter(
                    name="is_processed",
                    type="boolean",
                    description="是否已处理过滤",
                    required=False
                )
            ],
            category="monitor",
            handler=get_recent_comments
        )
        
        # 注册所有工具
        tools = [
            create_task_tool,
            start_task_tool,
            stop_task_tool,
            list_tasks_tool,
            task_stats_tool,
            recent_comments_tool
        ]
        
        for tool in tools:
            tool_registry.register_tool(tool)
        
        logger.info(f"监测模块工具注册完成，共注册 {len(tools)} 个工具")
        
    except Exception as e:
        logger.error(f"注册监测工具失败: {e}")
        raise
