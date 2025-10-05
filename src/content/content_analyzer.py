"""
内容分析引擎 - 负责热门内容分析和创作建议
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from loguru import logger
from playwright.async_api import Page

from ..auth.browser_manager import BrowserManager
from ..monitor.models import VideoData, CommentData
from ..config.database import get_db
from ..config.settings import settings


class ContentAnalyzer:
    """内容分析引擎主类"""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.legal_keywords = [
            "法律", "律师", "维权", "起诉", "合同", "纠纷", "诉讼", "判决",
            "赔偿", "责任", "违法", "犯罪", "民法", "刑法", "行政法",
            "劳动法", "婚姻法", "房产", "继承", "债务", "侵权"
        ]
        self.trending_topics = []
        logger.info("内容分析引擎初始化完成")
    
    async def analyze_trending_legal_content(self, limit: int = 20) -> Dict[str, Any]:
        """分析抖音上的热门法律内容"""
        try:
            await self.browser_manager.initialize()
            
            trending_videos = []
            search_keywords = ["法律知识", "律师普法", "法律科普", "维权"]
            
            for keyword in search_keywords:
                videos = await self._search_trending_videos(keyword, limit // len(search_keywords))
                trending_videos.extend(videos)
            
            # 分析视频内容
            analyzed_content = await self._analyze_video_content(trending_videos)
            
            # 生成趋势报告
            trends = self._generate_trend_analysis(analyzed_content)
            
            return {
                "success": True,
                "trending_videos": analyzed_content,
                "trend_analysis": trends,
                "analyzed_at": datetime.utcnow().isoformat(),
                "total_videos": len(analyzed_content)
            }
            
        except Exception as e:
            logger.error(f"分析热门法律内容失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_trending_videos(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """搜索热门视频"""
        try:
            page = await self.browser_manager.context.new_page()
            
            # 搜索关键词
            search_url = f"https://www.douyin.com/search/{keyword}?type=video"
            await page.goto(search_url, wait_until="networkidle")
            
            # 等待视频列表加载
            await page.wait_for_selector('.video-list, .result-list', timeout=10000)
            
            # 获取视频信息
            video_elements = await page.query_selector_all('.video-item, .result-item')
            videos = []
            
            for i, element in enumerate(video_elements[:limit]):
                try:
                    video_info = await self._extract_video_info(element, page)
                    if video_info:
                        video_info["search_keyword"] = keyword
                        videos.append(video_info)
                except Exception as e:
                    logger.warning(f"提取视频信息失败: {e}")
                    continue
            
            await page.close()
            return videos
            
        except Exception as e:
            logger.error(f"搜索热门视频失败 {keyword}: {e}")
            if 'page' in locals():
                await page.close()
            return []
    
    async def _extract_video_info(self, element, page: Page) -> Optional[Dict[str, Any]]:
        """提取视频信息"""
        try:
            # 视频链接
            link_element = await element.query_selector('a')
            video_url = await link_element.get_attribute('href') if link_element else ""
            
            # 视频标题/描述
            title_element = await element.query_selector('.title, .desc, .video-desc')
            title = await title_element.inner_text() if title_element else ""
            
            # 作者信息
            author_element = await element.query_selector('.author, .username')
            author = await author_element.inner_text() if author_element else ""
            
            # 互动数据
            like_element = await element.query_selector('.like-count, .digg-count')
            like_text = await like_element.inner_text() if like_element else "0"
            like_count = self._parse_count(like_text)
            
            comment_element = await element.query_selector('.comment-count')
            comment_text = await comment_element.inner_text() if comment_element else "0"
            comment_count = self._parse_count(comment_text)
            
            return {
                "video_url": video_url,
                "title": title.strip(),
                "author": author.strip(),
                "like_count": like_count,
                "comment_count": comment_count,
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"提取单个视频信息失败: {e}")
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """解析数量文本"""
        try:
            count_text = count_text.strip().replace('+', '')
            if '万' in count_text:
                return int(float(count_text.replace('万', '')) * 10000)
            elif 'w' in count_text.lower():
                return int(float(count_text.lower().replace('w', '')) * 10000)
            elif '千' in count_text:
                return int(float(count_text.replace('千', '')) * 1000)
            elif 'k' in count_text.lower():
                return int(float(count_text.lower().replace('k', '')) * 1000)
            else:
                # 提取数字
                numbers = re.findall(r'\d+', count_text)
                return int(numbers[0]) if numbers else 0
        except Exception:
            return 0
    
    async def _analyze_video_content(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析视频内容"""
        analyzed_videos = []
        
        for video in videos:
            try:
                analysis = {
                    **video,
                    "legal_topics": self._extract_legal_topics(video["title"]),
                    "content_type": self._classify_content_type(video["title"]),
                    "engagement_score": self._calculate_engagement_score(video),
                    "trending_potential": self._assess_trending_potential(video)
                }
                analyzed_videos.append(analysis)
                
            except Exception as e:
                logger.warning(f"分析视频内容失败: {e}")
                continue
        
        return analyzed_videos
    
    def _extract_legal_topics(self, title: str) -> List[str]:
        """提取法律主题"""
        topics = []
        title_lower = title.lower()
        
        topic_mapping = {
            "民事": ["民事", "合同", "债务", "侵权", "物权"],
            "刑事": ["刑事", "犯罪", "刑法", "判决", "量刑"],
            "劳动": ["劳动", "工伤", "加班", "辞职", "劳动合同"],
            "婚姻": ["婚姻", "离婚", "财产", "抚养", "赡养"],
            "房产": ["房产", "买房", "租房", "拆迁", "物业"],
            "交通": ["交通", "车祸", "事故", "赔偿", "保险"],
            "消费": ["消费", "退货", "维权", "投诉", "欺诈"]
        }
        
        for topic, keywords in topic_mapping.items():
            if any(keyword in title_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _classify_content_type(self, title: str) -> str:
        """分类内容类型"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["科普", "知识", "普法"]):
            return "科普教育"
        elif any(word in title_lower for word in ["案例", "真实", "故事"]):
            return "案例分析"
        elif any(word in title_lower for word in ["问答", "咨询", "解答"]):
            return "问答互动"
        elif any(word in title_lower for word in ["技巧", "方法", "如何"]):
            return "实用技巧"
        else:
            return "综合内容"
    
    def _calculate_engagement_score(self, video: Dict[str, Any]) -> float:
        """计算互动得分"""
        try:
            like_count = video.get("like_count", 0)
            comment_count = video.get("comment_count", 0)
            
            # 简单的互动得分计算
            engagement_score = (like_count * 0.7 + comment_count * 1.3) / 1000
            return round(min(engagement_score, 100), 2)
            
        except Exception:
            return 0.0
    
    def _assess_trending_potential(self, video: Dict[str, Any]) -> str:
        """评估热门潜力"""
        engagement_score = video.get("engagement_score", 0)
        
        if engagement_score >= 50:
            return "高"
        elif engagement_score >= 20:
            return "中"
        else:
            return "低"
    
    def _generate_trend_analysis(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成趋势分析"""
        if not videos:
            return {"message": "暂无数据"}
        
        # 热门主题统计
        all_topics = []
        for video in videos:
            all_topics.extend(video.get("legal_topics", []))
        
        topic_counter = Counter(all_topics)
        hot_topics = [{"topic": topic, "count": count} for topic, count in topic_counter.most_common(10)]
        
        # 内容类型分布
        content_types = [video.get("content_type", "其他") for video in videos]
        type_counter = Counter(content_types)
        type_distribution = [{"type": ctype, "count": count} for ctype, count in type_counter.items()]
        
        # 高互动视频
        high_engagement_videos = [
            video for video in videos 
            if video.get("engagement_score", 0) >= 20
        ]
        
        # 平均互动数据
        avg_likes = sum(v.get("like_count", 0) for v in videos) / len(videos) if videos else 0
        avg_comments = sum(v.get("comment_count", 0) for v in videos) / len(videos) if videos else 0
        
        return {
            "hot_topics": hot_topics,
            "content_type_distribution": type_distribution,
            "high_engagement_count": len(high_engagement_videos),
            "average_metrics": {
                "likes": round(avg_likes, 0),
                "comments": round(avg_comments, 0)
            },
            "trending_keywords": self._extract_trending_keywords(videos)
        }
    
    def _extract_trending_keywords(self, videos: List[Dict[str, Any]]) -> List[str]:
        """提取热门关键词"""
        all_titles = " ".join([video.get("title", "") for video in videos])
        
        # 简单的关键词提取
        words = re.findall(r'[\u4e00-\u9fff]+', all_titles)
        word_counter = Counter(words)
        
        # 过滤常见停用词
        stop_words = {"的", "了", "在", "是", "有", "和", "就", "都", "而", "及", "与", "这", "那", "你", "我", "他"}
        trending_words = [
            word for word, count in word_counter.most_common(20)
            if len(word) >= 2 and word not in stop_words
        ]
        
        return trending_words[:10]
    
    async def generate_content_suggestions(self, account_id: int, db: AsyncSession) -> Dict[str, Any]:
        """生成内容创作建议"""
        try:
            # 分析账号历史数据
            historical_analysis = await self._analyze_account_content_history(account_id, db)
            
            # 获取热门趋势
            trending_analysis = await self.analyze_trending_legal_content(15)
            
            # 分析竞品内容
            competitor_analysis = await self._analyze_competitor_content()
            
            # 生成创作建议
            suggestions = self._generate_creation_suggestions(
                historical_analysis, 
                trending_analysis, 
                competitor_analysis
            )
            
            return {
                "success": True,
                "suggestions": suggestions,
                "historical_analysis": historical_analysis,
                "trending_insights": trending_analysis.get("trend_analysis", {}),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成内容建议失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_account_content_history(self, account_id: int, db: AsyncSession) -> Dict[str, Any]:
        """分析账号内容历史"""
        try:
            # 获取账号的视频数据
            from ..monitor.models import MonitorTask
            
            videos_result = await db.execute(
                select(VideoData, CommentData.category, func.count(CommentData.id).label('comment_count'))
                .join(MonitorTask, VideoData.monitor_task_id == MonitorTask.id)
                .outerjoin(CommentData, CommentData.video_id == VideoData.id)
                .where(MonitorTask.account_id == account_id)
                .group_by(VideoData.id, CommentData.category)
                .order_by(VideoData.created_at.desc())
                .limit(50)
            )
            
            video_data = videos_result.all()
            
            if not video_data:
                return {"message": "暂无历史数据"}
            
            # 分析内容表现
            video_performance = []
            for video, category, comment_count in video_data:
                performance = {
                    "title": video.title,
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "comment_count": comment_count or 0,
                    "content_topics": self._extract_legal_topics(video.title or ""),
                    "content_type": self._classify_content_type(video.title or "")
                }
                video_performance.append(performance)
            
            # 统计最佳表现的内容类型
            best_performing = sorted(
                video_performance, 
                key=lambda x: x["like_count"] + x["comment_count"] * 2, 
                reverse=True
            )[:10]
            
            return {
                "total_videos": len(video_performance),
                "best_performing": best_performing,
                "content_insights": self._analyze_content_patterns(video_performance)
            }
            
        except Exception as e:
            logger.error(f"分析账号内容历史失败: {e}")
            return {"error": str(e)}
    
    def _analyze_content_patterns(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析内容模式"""
        if not videos:
            return {}
        
        # 内容类型效果分析
        type_performance = defaultdict(list)
        for video in videos:
            content_type = video.get("content_type", "其他")
            engagement = video.get("like_count", 0) + video.get("comment_count", 0) * 2
            type_performance[content_type].append(engagement)
        
        type_avg_performance = {}
        for ctype, performances in type_performance.items():
            type_avg_performance[ctype] = sum(performances) / len(performances) if performances else 0
        
        # 找出最佳内容类型
        best_type = max(type_avg_performance.items(), key=lambda x: x[1]) if type_avg_performance else ("无数据", 0)
        
        return {
            "content_type_performance": type_avg_performance,
            "best_content_type": best_type[0],
            "best_type_avg_engagement": round(best_type[1], 2)
        }
    
    async def _analyze_competitor_content(self) -> Dict[str, Any]:
        """分析竞品内容（简化版）"""
        # 这里可以实现更复杂的竞品分析逻辑
        return {
            "competitor_topics": ["劳动法", "民事纠纷", "消费维权"],
            "trending_formats": ["案例分析", "问答解释", "法条解读"],
            "optimal_posting_times": ["19:00-21:00", "12:00-14:00"]
        }
    
    def _generate_creation_suggestions(self, historical: Dict, trending: Dict, competitor: Dict) -> List[Dict[str, Any]]:
        """生成创作建议"""
        suggestions = []
        
        # 基于热门趋势的建议
        if trending.get("success") and trending.get("trend_analysis"):
            trend_analysis = trending["trend_analysis"]
            hot_topics = trend_analysis.get("hot_topics", [])
            
            if hot_topics:
                top_topic = hot_topics[0]
                suggestions.append({
                    "type": "热门话题",
                    "title": f"关注 '{top_topic['topic']}' 相关内容",
                    "description": f"该话题当前热度较高，出现了 {top_topic['count']} 次",
                    "priority": "高",
                    "suggested_content": f"可以制作关于{top_topic['topic']}的科普或案例分析视频"
                })
        
        # 基于历史表现的建议
        if historical.get("content_insights"):
            insights = historical["content_insights"]
            best_type = insights.get("best_content_type")
            if best_type and best_type != "无数据":
                suggestions.append({
                    "type": "优势内容",
                    "title": f"继续发布 '{best_type}' 类型内容",
                    "description": f"该类型内容在您的账号上表现最佳",
                    "priority": "中",
                    "suggested_content": f"基于历史数据，{best_type}类型的内容更受您的粉丝欢迎"
                })
        
        # 内容创新建议
        suggestions.extend([
            {
                "type": "内容创新",
                "title": "结合时事热点",
                "description": "将法律知识与当前社会热点结合",
                "priority": "中",
                "suggested_content": "关注社会热点事件，从法律角度进行专业解读"
            },
            {
                "type": "互动增强",
                "title": "增加互动问答",
                "description": "在视频中设置问题引导评论互动",
                "priority": "中",
                "suggested_content": "视频结尾提出法律相关问题，邀请观众评论讨论"
            },
            {
                "type": "系列内容",
                "title": "制作系列普法内容",
                "description": "围绕一个主题制作系列内容",
                "priority": "低",
                "suggested_content": "如'劳动者权益保护系列'、'消费维权指南系列'等"
            }
        ])
        
        return suggestions


# 全局内容分析引擎实例
content_analyzer = ContentAnalyzer()
