"""
监测引擎 - 负责抖音内容的智能监测
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urlparse, parse_qs

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from loguru import logger
from playwright.async_api import Page, Browser

from .models import (
    MonitorTask, VideoData, CommentData, MonitorStatus, 
    MonitorTaskCreate, MonitorTaskUpdate, CommentType
)
from .exceptions import (
    MonitorError, TaskNotFoundError, TaskAlreadyRunningError,
    ScrapingError, RateLimitExceededError, LoginRequiredError
)
from ..auth.browser_manager import BrowserManager
from ..config.database import get_db
from ..config.redis_config import get_redis
from ..config.settings import settings


class MonitorEngine:
    """监测引擎主类"""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self._running_tasks: Dict[int, asyncio.Task] = {}
        self._task_stats: Dict[int, Dict[str, Any]] = {}
        self._last_check_times: Dict[int, datetime] = {}
        logger.info("监测引擎初始化完成")
    
    async def create_monitor_task(self, task_data: MonitorTaskCreate, db: AsyncSession) -> MonitorTask:
        """创建监测任务"""
        try:
            # 检查账号是否存在
            from ..auth.auth_manager import AuthManager
            auth_manager = AuthManager()
            account = await auth_manager.get_account_by_id(task_data.account_id, db)
            if not account:
                raise MonitorError(f"账号 {task_data.account_id} 不存在")
            
            # 创建任务
            task = MonitorTask(
                account_id=task_data.account_id,
                task_name=task_data.task_name,
                description=task_data.description,
                monitor_videos=task_data.monitor_videos,
                monitor_comments=task_data.monitor_comments,
                monitor_messages=task_data.monitor_messages,
                monitor_mentions=task_data.monitor_mentions,
                keywords=task_data.keywords,
                exclude_keywords=task_data.exclude_keywords,
                check_interval=task_data.check_interval,
                max_videos_per_check=task_data.max_videos_per_check,
                min_comment_length=task_data.min_comment_length,
                max_comment_length=task_data.max_comment_length,
                filter_spam=task_data.filter_spam,
                status=MonitorStatus.ACTIVE.value,
                next_check_at=datetime.utcnow() + timedelta(seconds=task_data.check_interval)
            )
            
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            # 初始化任务统计
            self._task_stats[task.id] = {
                "videos_checked": 0,
                "comments_found": 0,
                "errors": 0,
                "last_error": None
            }
            
            logger.info(f"创建监测任务成功: {task.task_name} (ID: {task.id})")
            return task
            
        except Exception as e:
            await db.rollback()
            if isinstance(e, MonitorError):
                raise
            logger.error(f"创建监测任务失败: {e}")
            raise MonitorError(f"创建监测任务失败: {e}")
    
    async def start_monitor_task(self, task_id: int, db: AsyncSession) -> bool:
        """启动监测任务"""
        try:
            # 检查任务是否存在
            task = await self.get_monitor_task(task_id, db)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查任务是否已在运行
            if task_id in self._running_tasks:
                raise TaskAlreadyRunningError(task_id)
            
            # 更新任务状态
            await db.execute(
                update(MonitorTask)
                .where(MonitorTask.id == task_id)
                .values(
                    status=MonitorStatus.ACTIVE.value,
                    updated_at=datetime.utcnow(),
                    next_check_at=datetime.utcnow() + timedelta(seconds=task.check_interval)
                )
            )
            await db.commit()
            
            # 启动监测任务
            monitor_task = asyncio.create_task(self._run_monitor_loop(task_id))
            self._running_tasks[task_id] = monitor_task
            
            logger.info(f"启动监测任务: {task.task_name} (ID: {task_id})")
            return True
            
        except Exception as e:
            if isinstance(e, MonitorError):
                raise
            logger.error(f"启动监测任务失败: {e}")
            raise MonitorError(f"启动监测任务失败: {e}")
    
    async def stop_monitor_task(self, task_id: int, db: AsyncSession) -> bool:
        """停止监测任务"""
        try:
            # 停止运行中的任务
            if task_id in self._running_tasks:
                task = self._running_tasks[task_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._running_tasks[task_id]
            
            # 更新任务状态
            await db.execute(
                update(MonitorTask)
                .where(MonitorTask.id == task_id)
                .values(
                    status=MonitorStatus.STOPPED.value,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"停止监测任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止监测任务失败: {e}")
            raise MonitorError(f"停止监测任务失败: {e}")
    
    async def _run_monitor_loop(self, task_id: int) -> None:
        """监测任务主循环"""
        logger.info(f"开始监测任务循环: {task_id}")
        
        while True:
            try:
                async for db in get_db():
                    # 获取任务信息
                    task = await self.get_monitor_task(task_id, db)
                    if not task or task.status != MonitorStatus.ACTIVE.value:
                        logger.info(f"任务 {task_id} 已停止或不存在")
                        break
                    
                    # 检查是否到了执行时间
                    now = datetime.utcnow()
                    if task.next_check_at and now < task.next_check_at:
                        await asyncio.sleep(min(60, (task.next_check_at - now).total_seconds()))
                        continue
                    
                    # 执行监测
                    try:
                        await self._execute_monitor_check(task, db)
                        
                        # 更新下次检查时间
                        next_check = now + timedelta(seconds=task.check_interval)
                        await db.execute(
                            update(MonitorTask)
                            .where(MonitorTask.id == task_id)
                            .values(
                                last_check_at=now,
                                next_check_at=next_check,
                                updated_at=now
                            )
                        )
                        await db.commit()
                        
                    except Exception as e:
                        logger.error(f"监测任务 {task_id} 执行失败: {e}")
                        
                        # 更新错误统计
                        if task_id in self._task_stats:
                            self._task_stats[task_id]["errors"] += 1
                            self._task_stats[task_id]["last_error"] = str(e)
                        
                        # 如果连续失败过多，暂停任务
                        if self._task_stats.get(task_id, {}).get("errors", 0) > 5:
                            await db.execute(
                                update(MonitorTask)
                                .where(MonitorTask.id == task_id)
                                .values(status=MonitorStatus.ERROR.value)
                            )
                            await db.commit()
                            logger.error(f"任务 {task_id} 连续失败过多，自动暂停")
                            break
                    
                    # 等待下次检查
                    await asyncio.sleep(min(60, task.check_interval))
                    
            except asyncio.CancelledError:
                logger.info(f"监测任务 {task_id} 被取消")
                break
            except Exception as e:
                logger.error(f"监测任务循环异常 {task_id}: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _execute_monitor_check(self, task: MonitorTask, db: AsyncSession) -> None:
        """执行一次监测检查"""
        logger.info(f"执行监测检查: {task.task_name}")
        
        try:
            # 初始化浏览器
            await self.browser_manager.initialize()
            
            # 获取账号最新视频
            if task.monitor_videos:
                videos = await self._get_latest_videos(task, db)
                
                # 检查视频评论
                if task.monitor_comments:
                    for video in videos[:task.max_videos_per_check]:
                        await self._check_video_comments(task, video, db)
                        await asyncio.sleep(6)  # 避免请求过频
            
            # 检查私信（如果启用）
            if task.monitor_messages:
                await self._check_private_messages(task, db)
            
            # 检查@提及（如果启用）
            if task.monitor_mentions:
                await self._check_mentions(task, db)
            
            # 更新统计
            if task.id in self._task_stats:
                self._task_stats[task.id]["errors"] = 0  # 重置错误计数
            
        except Exception as e:
            logger.error(f"监测检查失败 {task.id}: {e}")
            raise
    
    async def _get_latest_videos(self, task: MonitorTask, db: AsyncSession) -> List[VideoData]:
        """获取最新视频列表"""
        try:
            # 创建新页面
            page = await self.browser_manager.context.new_page()
            
            # 访问用户主页（这里需要根据实际账号信息构建URL）
            await page.goto(f"https://www.douyin.com/user/self", wait_until="networkidle")
            
            # 检查登录状态
            if "passport" in page.url:
                raise LoginRequiredError(task.account_id)
            
            # 获取视频列表
            video_elements = await page.query_selector_all('.video-item, .aweme-item')
            videos = []
            
            for element in video_elements:
                try:
                    # 提取视频信息
                    video_link = await element.query_selector('a')
                    if video_link:
                        video_url = await video_link.get_attribute('href')
                        if video_url:
                            video_id = self._extract_video_id(video_url)
                            
                            # 检查视频是否已存在
                            existing_video = await db.execute(
                                select(VideoData).where(VideoData.video_id == video_id)
                            )
                            if existing_video.scalar_one_or_none():
                                continue
                            
                            # 获取视频标题和统计数据
                            title_element = await element.query_selector('.title, .desc')
                            title = await title_element.inner_text() if title_element else ""
                            
                            # 创建新视频记录
                            video = VideoData(
                                monitor_task_id=task.id,
                                video_id=video_id,
                                video_url=video_url,
                                title=title,
                                is_monitored=True,
                                last_monitored_at=datetime.utcnow()
                            )
                            
                            db.add(video)
                            videos.append(video)
                            
                except Exception as e:
                    logger.warning(f"解析视频元素失败: {e}")
                    continue
            
            await db.commit()
            await page.close()
            
            logger.info(f"获取到 {len(videos)} 个新视频")
            return videos
            
        except Exception as e:
            if 'page' in locals():
                await page.close()
            logger.error(f"获取视频列表失败: {e}")
            raise ScrapingError(f"获取视频列表失败: {e}")
    
    async def _check_video_comments(self, task: MonitorTask, video: VideoData, db: AsyncSession) -> None:
        """检查视频评论"""
        try:
            page = await self.browser_manager.context.new_page()
            await page.goto(video.video_url, wait_until="networkidle")
            
            # 等待评论加载
            await page.wait_for_selector('.comment-list, .comments', timeout=10000)
            
            # 获取评论列表
            comment_elements = await page.query_selector_all('.comment-item, .comment')
            
            for element in comment_elements:
                try:
                    # 提取评论信息
                    content_element = await element.query_selector('.comment-text, .content')
                    if not content_element:
                        continue
                    
                    content = await content_element.inner_text()
                    content = content.strip()
                    
                    # 过滤评论
                    if not self._should_process_comment(content, task):
                        continue
                    
                    # 获取评论ID
                    comment_id = await element.get_attribute('data-id')
                    if not comment_id:
                        comment_id = f"comment_{hash(content)}_{int(datetime.now().timestamp())}"
                    
                    # 检查评论是否已存在
                    existing_comment = await db.execute(
                        select(CommentData).where(CommentData.comment_id == comment_id)
                    )
                    if existing_comment.scalar_one_or_none():
                        continue
                    
                    # 获取评论者信息
                    author_element = await element.query_selector('.author, .username')
                    author_name = await author_element.inner_text() if author_element else "未知用户"
                    
                    # 获取点赞数
                    like_element = await element.query_selector('.like-count, .digg-count')
                    like_count = 0
                    if like_element:
                        like_text = await like_element.inner_text()
                        like_count = self._parse_count(like_text)
                    
                    # 分类评论
                    category = self._classify_comment(content, task.keywords or [])
                    keywords_matched = self._extract_matched_keywords(content, task.keywords or [])
                    
                    # 创建评论记录
                    comment = CommentData(
                        monitor_task_id=task.id,
                        video_id=video.id,
                        comment_id=comment_id,
                        content=content,
                        comment_type=CommentType.COMMENT.value,
                        author_name=author_name,
                        like_count=like_count,
                        category=category,
                        keywords_matched=keywords_matched,
                        is_processed=False,
                        comment_time=datetime.utcnow()
                    )
                    
                    db.add(comment)
                    
                    # 更新任务统计
                    if task.id in self._task_stats:
                        self._task_stats[task.id]["comments_found"] += 1
                    
                except Exception as e:
                    logger.warning(f"解析评论失败: {e}")
                    continue
            
            await db.commit()
            await page.close()
            
        except Exception as e:
            if 'page' in locals():
                await page.close()
            logger.error(f"检查视频评论失败: {e}")
            raise ScrapingError(f"检查视频评论失败: {e}")
    
    async def _check_private_messages(self, task: MonitorTask, db: AsyncSession) -> None:
        """检查私信消息"""
        # 这里实现私信检查逻辑
        # 由于私信接口的复杂性，这里先实现基础框架
        logger.info(f"检查私信 - 任务 {task.id}")
        pass
    
    async def _check_mentions(self, task: MonitorTask, db: AsyncSession) -> None:
        """检查@提及"""
        # 这里实现@提及检查逻辑
        logger.info(f"检查@提及 - 任务 {task.id}")
        pass
    
    def _extract_video_id(self, video_url: str) -> str:
        """从URL中提取视频ID"""
        try:
            # 解析URL获取视频ID
            if "/video/" in video_url:
                video_id = video_url.split("/video/")[1].split("?")[0]
            else:
                # 备用解析方法
                parsed = urlparse(video_url)
                video_id = parsed.path.split("/")[-1]
            
            return video_id
        except Exception:
            return f"video_{int(datetime.now().timestamp())}"
    
    def _should_process_comment(self, content: str, task: MonitorTask) -> bool:
        """判断是否应该处理该评论"""
        # 长度过滤
        if len(content) < task.min_comment_length or len(content) > task.max_comment_length:
            return False
        
        # 垃圾评论过滤
        if task.filter_spam and self._is_spam_comment(content):
            return False
        
        # 排除关键词过滤
        if task.exclude_keywords:
            for keyword in task.exclude_keywords:
                if keyword.lower() in content.lower():
                    return False
        
        # 关键词匹配（如果设置了关键词）
        if task.keywords:
            for keyword in task.keywords:
                if keyword.lower() in content.lower():
                    return True
            return False  # 设置了关键词但都不匹配
        
        return True
    
    def _is_spam_comment(self, content: str) -> bool:
        """判断是否为垃圾评论"""
        spam_patterns = [
            r'加.*微信',
            r'联系.*微信',
            r'咨询.*微信', 
            r'广告',
            r'推广',
            r'刷.*粉',
            r'买.*粉',
            r'代.*刷',
            r'www\.',
            r'http[s]?://'
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _classify_comment(self, content: str, keywords: List[str]) -> str:
        """分类评论内容"""
        content_lower = content.lower()
        
        # 法律咨询相关
        legal_keywords = ["咨询", "法律", "律师", "维权", "起诉", "合同", "纠纷"]
        if any(keyword in content_lower for keyword in legal_keywords):
            return "法律咨询"
        
        # 感谢赞扬
        praise_keywords = ["谢谢", "感谢", "厉害", "专业", "棒", "赞"]
        if any(keyword in content_lower for keyword in praise_keywords):
            return "感谢赞扬"
        
        # 质疑反驳
        doubt_keywords = ["不对", "错误", "质疑", "反对", "不同意"]
        if any(keyword in content_lower for keyword in doubt_keywords):
            return "质疑反驳"
        
        # 问号结尾通常是问题
        if content.endswith("?") or content.endswith("？"):
            return "咨询问题"
        
        return "普通互动"
    
    def _extract_matched_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """提取匹配的关键词"""
        matched = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched.append(keyword)
        
        return matched
    
    def _parse_count(self, count_text: str) -> int:
        """解析数量文本"""
        try:
            count_text = count_text.strip()
            if "万" in count_text:
                return int(float(count_text.replace("万", "")) * 10000)
            elif "千" in count_text:
                return int(float(count_text.replace("千", "")) * 1000)
            else:
                return int(re.sub(r'[^\d]', '', count_text) or "0")
        except Exception:
            return 0
    
    async def get_monitor_task(self, task_id: int, db: AsyncSession) -> Optional[MonitorTask]:
        """获取监测任务"""
        try:
            result = await db.execute(
                select(MonitorTask).where(MonitorTask.id == task_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取监测任务失败: {e}")
            return None
    
    async def list_monitor_tasks(self, db: AsyncSession, account_id: Optional[int] = None) -> List[MonitorTask]:
        """列出监测任务"""
        try:
            query = select(MonitorTask).order_by(MonitorTask.created_at.desc())
            if account_id:
                query = query.where(MonitorTask.account_id == account_id)
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取监测任务列表失败: {e}")
            return []
    
    async def get_task_statistics(self, task_id: int, db: AsyncSession) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            task = await self.get_monitor_task(task_id, db)
            if not task:
                return {}
            
            # 运行时统计
            runtime_stats = self._task_stats.get(task_id, {})
            
            # 数据库统计
            video_count_result = await db.execute(
                select(VideoData.id).where(VideoData.monitor_task_id == task_id).count()
            )
            video_count = video_count_result.scalar()
            
            comment_count_result = await db.execute(
                select(CommentData.id).where(CommentData.monitor_task_id == task_id).count()
            )
            comment_count = comment_count_result.scalar()
            
            return {
                "task_id": task_id,
                "task_name": task.task_name,
                "status": task.status,
                "is_running": task_id in self._running_tasks,
                "total_videos": video_count or 0,
                "total_comments": comment_count or 0,
                "total_replies": task.total_replies_sent,
                "runtime_stats": runtime_stats,
                "last_check_at": task.last_check_at.isoformat() if task.last_check_at else None,
                "next_check_at": task.next_check_at.isoformat() if task.next_check_at else None
            }
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止所有运行中的任务
            for task_id, task in list(self._running_tasks.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self._running_tasks.clear()
            
            # 清理浏览器资源
            await self.browser_manager.cleanup()
            
            logger.info("监测引擎资源清理完成")
            
        except Exception as e:
            logger.error(f"监测引擎清理失败: {e}")


# 全局监测引擎实例
monitor_engine = MonitorEngine()
