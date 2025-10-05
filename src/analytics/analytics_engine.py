"""
数据分析引擎 - 负责数据统计分析和报告生成
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from loguru import logger

from ..monitor.models import MonitorTask, VideoData, CommentData
from ..reply.models import ReplyRecord, ReplyTemplate, ReplyStatus
from ..auth.models import DouyinAccount
from ..config.database import get_db


class AnalyticsEngine:
    """数据分析引擎主类"""
    
    def __init__(self):
        logger.info("数据分析引擎初始化完成")
    
    async def get_account_overview(self, account_id: int, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """获取账号概览数据"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 账号基本信息
            account_result = await db.execute(
                select(DouyinAccount).where(DouyinAccount.id == account_id)
            )
            account = account_result.scalar_one_or_none()
            
            if not account:
                return {"error": f"账号 {account_id} 不存在"}
            
            # 监测任务统计
            tasks_result = await db.execute(
                select(func.count(MonitorTask.id))
                .where(MonitorTask.account_id == account_id)
            )
            total_tasks = tasks_result.scalar() or 0
            
            # 活跃任务统计
            active_tasks_result = await db.execute(
                select(func.count(MonitorTask.id))
                .where(and_(
                    MonitorTask.account_id == account_id,
                    MonitorTask.status == "active"
                ))
            )
            active_tasks = active_tasks_result.scalar() or 0
            
            # 视频统计
            videos_result = await db.execute(
                select(func.count(VideoData.id))
                .join(MonitorTask, VideoData.monitor_task_id == MonitorTask.id)
                .where(and_(
                    MonitorTask.account_id == account_id,
                    VideoData.created_at >= start_date
                ))
            )
            videos_monitored = videos_result.scalar() or 0
            
            # 评论统计
            comments_result = await db.execute(
                select(func.count(CommentData.id))
                .join(MonitorTask, CommentData.monitor_task_id == MonitorTask.id)
                .where(and_(
                    MonitorTask.account_id == account_id,
                    CommentData.created_at >= start_date
                ))
            )
            comments_found = comments_result.scalar() or 0
            
            # 回复统计
            replies_result = await db.execute(
                select(func.count(ReplyRecord.id))
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.created_at >= start_date
                ))
            )
            replies_sent = replies_result.scalar() or 0
            
            # 成功回复统计
            successful_replies_result = await db.execute(
                select(func.count(ReplyRecord.id))
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.status == ReplyStatus.SENT.value,
                    ReplyRecord.created_at >= start_date
                ))
            )
            successful_replies = successful_replies_result.scalar() or 0
            
            # 计算成功率
            success_rate = (successful_replies / replies_sent * 100) if replies_sent > 0 else 0
            
            return {
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "nickname": account.nickname,
                    "status": account.status,
                    "follower_count": account.follower_count,
                    "following_count": account.following_count,
                    "video_count": account.video_count
                },
                "overview": {
                    "total_tasks": total_tasks,
                    "active_tasks": active_tasks,
                    "videos_monitored": videos_monitored,
                    "comments_found": comments_found,
                    "replies_sent": replies_sent,
                    "successful_replies": successful_replies,
                    "success_rate": round(success_rate, 2)
                },
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取账号概览失败: {e}")
            return {"error": str(e)}
    
    async def get_engagement_trends(self, account_id: int, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """获取互动趋势数据"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 按日期分组的评论数据
            daily_comments = await db.execute(
                select(
                    func.date(CommentData.created_at).label('date'),
                    func.count(CommentData.id).label('count')
                )
                .join(MonitorTask, CommentData.monitor_task_id == MonitorTask.id)
                .where(and_(
                    MonitorTask.account_id == account_id,
                    CommentData.created_at >= start_date
                ))
                .group_by(func.date(CommentData.created_at))
                .order_by(func.date(CommentData.created_at))
            )
            
            # 按日期分组的回复数据
            daily_replies = await db.execute(
                select(
                    func.date(ReplyRecord.created_at).label('date'),
                    func.count(ReplyRecord.id).label('count')
                )
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.created_at >= start_date
                ))
                .group_by(func.date(ReplyRecord.created_at))
                .order_by(func.date(ReplyRecord.created_at))
            )
            
            # 构建趋势数据
            comment_trends = {}
            for row in daily_comments:
                comment_trends[row.date.isoformat()] = row.count
            
            reply_trends = {}
            for row in daily_replies:
                reply_trends[row.date.isoformat()] = row.count
            
            # 生成完整的日期序列
            trends = []
            current_date = start_date.date()
            while current_date <= end_date.date():
                date_str = current_date.isoformat()
                trends.append({
                    "date": date_str,
                    "comments": comment_trends.get(date_str, 0),
                    "replies": reply_trends.get(date_str, 0)
                })
                current_date += timedelta(days=1)
            
            return {
                "success": True,
                "trends": trends,
                "summary": {
                    "total_comments": sum(comment_trends.values()),
                    "total_replies": sum(reply_trends.values()),
                    "avg_daily_comments": sum(comment_trends.values()) / days if days > 0 else 0,
                    "avg_daily_replies": sum(reply_trends.values()) / days if days > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取互动趋势失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_comment_categories_analysis(self, account_id: int, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """获取评论分类分析"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 按分类统计评论
            category_stats = await db.execute(
                select(
                    CommentData.category,
                    func.count(CommentData.id).label('count'),
                    func.avg(CommentData.like_count).label('avg_likes')
                )
                .join(MonitorTask, CommentData.monitor_task_id == MonitorTask.id)
                .where(and_(
                    MonitorTask.account_id == account_id,
                    CommentData.created_at >= start_date,
                    CommentData.category.isnot(None)
                ))
                .group_by(CommentData.category)
                .order_by(desc(func.count(CommentData.id)))
            )
            
            categories = []
            total_comments = 0
            
            for row in category_stats:
                count = row.count
                total_comments += count
                categories.append({
                    "category": row.category,
                    "count": count,
                    "avg_likes": round(row.avg_likes or 0, 2)
                })
            
            # 计算百分比
            for category in categories:
                category["percentage"] = round(category["count"] / total_comments * 100, 2) if total_comments > 0 else 0
            
            return {
                "success": True,
                "categories": categories,
                "total_comments": total_comments
            }
            
        except Exception as e:
            logger.error(f"获取评论分类分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_template_performance(self, account_id: int, db: AsyncSession) -> Dict[str, Any]:
        """获取模板使用效果分析"""
        try:
            # 模板使用统计
            template_stats = await db.execute(
                select(
                    ReplyTemplate.id,
                    ReplyTemplate.template_name,
                    ReplyTemplate.category,
                    ReplyTemplate.usage_count,
                    ReplyTemplate.success_rate,
                    func.count(ReplyRecord.id).label('recent_usage')
                )
                .outerjoin(
                    ReplyRecord,
                    and_(
                        ReplyRecord.template_id == ReplyTemplate.id,
                        ReplyRecord.created_at >= datetime.utcnow() - timedelta(days=30)
                    )
                )
                .where(ReplyTemplate.account_id == account_id)
                .group_by(
                    ReplyTemplate.id,
                    ReplyTemplate.template_name,
                    ReplyTemplate.category,
                    ReplyTemplate.usage_count,
                    ReplyTemplate.success_rate
                )
                .order_by(desc(ReplyTemplate.usage_count))
            )
            
            templates = []
            for row in template_stats:
                templates.append({
                    "id": row.id,
                    "template_name": row.template_name,
                    "category": row.category,
                    "total_usage": row.usage_count,
                    "recent_usage": row.recent_usage,
                    "success_rate": round(row.success_rate or 0, 2)
                })
            
            # 分类统计
            category_usage = defaultdict(int)
            for template in templates:
                category_usage[template["category"]] += template["total_usage"]
            
            return {
                "success": True,
                "templates": templates,
                "category_usage": dict(category_usage),
                "total_templates": len(templates)
            }
            
        except Exception as e:
            logger.error(f"获取模板效果分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_conversion_analysis(self, account_id: int, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """获取转化分析"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 总回复数
            total_replies_result = await db.execute(
                select(func.count(ReplyRecord.id))
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.created_at >= start_date
                ))
            )
            total_replies = total_replies_result.scalar() or 0
            
            # 转化结果统计
            conversion_stats = await db.execute(
                select(
                    ReplyRecord.conversion_result,
                    func.count(ReplyRecord.id).label('count')
                )
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.created_at >= start_date,
                    ReplyRecord.conversion_result.isnot(None)
                ))
                .group_by(ReplyRecord.conversion_result)
            )
            
            conversions = {}
            total_conversions = 0
            
            for row in conversion_stats:
                count = row.count
                conversions[row.conversion_result] = count
                total_conversions += count
            
            # 计算转化率
            conversion_rate = (total_conversions / total_replies * 100) if total_replies > 0 else 0
            
            # 按评论分类的转化分析
            category_conversion = await db.execute(
                select(
                    ReplyRecord.comment_category,
                    func.count(ReplyRecord.id).label('total'),
                    func.sum(
                        func.case(
                            (ReplyRecord.conversion_result.isnot(None), 1),
                            else_=0
                        )
                    ).label('converted')
                )
                .where(and_(
                    ReplyRecord.account_id == account_id,
                    ReplyRecord.created_at >= start_date,
                    ReplyRecord.comment_category.isnot(None)
                ))
                .group_by(ReplyRecord.comment_category)
            )
            
            category_conversions = []
            for row in category_conversion:
                total = row.total
                converted = row.converted or 0
                category_rate = (converted / total * 100) if total > 0 else 0
                
                category_conversions.append({
                    "category": row.comment_category,
                    "total_replies": total,
                    "conversions": converted,
                    "conversion_rate": round(category_rate, 2)
                })
            
            return {
                "success": True,
                "overall": {
                    "total_replies": total_replies,
                    "total_conversions": total_conversions,
                    "conversion_rate": round(conversion_rate, 2)
                },
                "conversion_types": conversions,
                "category_analysis": category_conversions
            }
            
        except Exception as e:
            logger.error(f"获取转化分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_comprehensive_report(self, account_id: int, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """生成综合分析报告"""
        try:
            logger.info(f"生成账号 {account_id} 的综合分析报告")
            
            # 并行获取各项分析数据
            overview = await self.get_account_overview(account_id, db, days)
            trends = await self.get_engagement_trends(account_id, db, days)
            categories = await self.get_comment_categories_analysis(account_id, db, days)
            templates = await self.get_template_performance(account_id, db)
            conversions = await self.get_conversion_analysis(account_id, db, days)
            
            # 生成关键洞察
            insights = self._generate_insights(overview, trends, categories, templates, conversions)
            
            # 生成建议
            recommendations = self._generate_recommendations(overview, trends, categories, templates, conversions)
            
            report = {
                "success": True,
                "report_meta": {
                    "account_id": account_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "period_days": days,
                    "report_version": "1.0"
                },
                "overview": overview,
                "engagement_trends": trends,
                "comment_categories": categories,
                "template_performance": templates,
                "conversion_analysis": conversions,
                "insights": insights,
                "recommendations": recommendations
            }
            
            logger.info(f"综合分析报告生成完成: 账号 {account_id}")
            return report
            
        except Exception as e:
            logger.error(f"生成综合分析报告失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_insights(self, overview: Dict, trends: Dict, categories: Dict, templates: Dict, conversions: Dict) -> List[str]:
        """生成数据洞察"""
        insights = []
        
        try:
            # 账号活跃度洞察
            if overview.get("overview"):
                ov = overview["overview"]
                if ov["active_tasks"] == 0:
                    insights.append("⚠️ 当前没有活跃的监测任务，建议启动监测以获取更多数据")
                elif ov["success_rate"] < 50:
                    insights.append(f"📊 回复成功率为 {ov['success_rate']}%，建议优化回复策略")
                elif ov["success_rate"] > 80:
                    insights.append(f"✅ 回复成功率达到 {ov['success_rate']}%，表现优秀")
            
            # 趋势洞察
            if trends.get("success") and trends.get("trends"):
                trend_data = trends["trends"]
                if len(trend_data) >= 7:
                    recent_comments = sum(d["comments"] for d in trend_data[-7:])
                    previous_comments = sum(d["comments"] for d in trend_data[-14:-7]) if len(trend_data) >= 14 else 0
                    
                    if recent_comments > previous_comments * 1.2:
                        insights.append("📈 近期评论量显著增长，互动热度上升")
                    elif recent_comments < previous_comments * 0.8:
                        insights.append("📉 近期评论量有所下降，可考虑调整内容策略")
            
            # 分类洞察
            if categories.get("success") and categories.get("categories"):
                cats = categories["categories"]
                if cats:
                    top_category = cats[0]
                    insights.append(f"🏆 '{top_category['category']}' 是最主要的评论类型，占比 {top_category['percentage']}%")
                    
                    legal_categories = [c for c in cats if "法律" in c["category"] or "咨询" in c["category"]]
                    if legal_categories:
                        legal_total = sum(c["count"] for c in legal_categories)
                        total = categories["total_comments"]
                        legal_percentage = (legal_total / total * 100) if total > 0 else 0
                        insights.append(f"⚖️ 法律咨询类评论占比 {legal_percentage:.1f}%，专业定位明确")
            
            # 模板效果洞察
            if templates.get("success") and templates.get("templates"):
                temp_list = templates["templates"]
                if temp_list:
                    best_template = max(temp_list, key=lambda x: x["success_rate"])
                    if best_template["success_rate"] > 0:
                        insights.append(f"🎯 '{best_template['template_name']}' 模板效果最佳，成功率 {best_template['success_rate']}%")
        
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            insights.append("数据洞察生成过程中遇到问题，请检查数据完整性")
        
        return insights if insights else ["📋 数据收集中，暂无足够信息生成洞察"]
    
    def _generate_recommendations(self, overview: Dict, trends: Dict, categories: Dict, templates: Dict, conversions: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        try:
            # 基于成功率的建议
            if overview.get("overview"):
                success_rate = overview["overview"].get("success_rate", 0)
                if success_rate < 70:
                    recommendations.append("🔧 建议优化回复模板，提高回复质量和相关性")
                    recommendations.append("🎯 分析失败回复的原因，调整回复策略")
            
            # 基于分类分布的建议
            if categories.get("success") and categories.get("categories"):
                cats = categories["categories"]
                if len(cats) >= 2:
                    top_two = cats[:2]
                    if top_two[0]["percentage"] > 60:
                        recommendations.append(f"📊 {top_two[0]['category']} 类评论占主导，建议针对性优化该类型的回复策略")
                
                # 检查是否有足够的法律咨询类评论
                legal_cats = [c for c in cats if "法律" in c["category"] or "咨询" in c["category"]]
                if not legal_cats or sum(c["count"] for c in legal_cats) < categories["total_comments"] * 0.3:
                    recommendations.append("⚖️ 法律咨询类评论比例较低，建议加强专业内容输出，吸引目标用户")
            
            # 基于模板使用的建议
            if templates.get("success") and templates.get("templates"):
                temp_list = templates["templates"]
                if len(temp_list) < 5:
                    recommendations.append("📝 回复模板数量较少，建议增加更多类型的模板以应对不同场景")
                
                low_usage_templates = [t for t in temp_list if t["recent_usage"] == 0 and t["total_usage"] < 5]
                if low_usage_templates:
                    recommendations.append("🗑️ 部分模板使用率较低，建议优化或删除无效模板")
            
            # 基于转化的建议
            if conversions.get("success"):
                conv_rate = conversions["overall"].get("conversion_rate", 0)
                if conv_rate < 10:
                    recommendations.append("💡 转化率较低，建议在回复中增加更明确的行动召唤")
                    recommendations.append("🎨 优化回复内容，提升用户参与意愿")
            
            # 通用建议
            recommendations.extend([
                "📱 定期关注抖音平台政策变化，确保合规运营",
                "📈 建议每周查看数据报告，及时调整运营策略",
                "🤝 积极与高质量评论用户互动，建立良好的社区关系"
            ])
        
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            recommendations.append("建议生成过程中遇到问题，请手动分析数据制定策略")
        
        return recommendations


# 全局分析引擎实例
analytics_engine = AnalyticsEngine()
