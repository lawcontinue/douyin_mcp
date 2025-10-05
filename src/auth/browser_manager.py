"""
浏览器管理器 - 负责抖音网页端的自动化操作
"""

import asyncio
import base64
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from .exceptions import BrowserError, LoginError, QRCodeExpiredError
from ..config.settings import settings


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._initialized = False
        self._login_pages: Dict[str, Page] = {}  # 存储登录页面
        
    async def initialize(self) -> None:
        """初始化浏览器"""
        if self._initialized:
            return
            
        try:
            self.playwright = await async_playwright().start()
            
            # 浏览器配置
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            
            if settings.PROXY_ENABLED and settings.PROXY_URL:
                proxy_config = {"server": settings.PROXY_URL}
                if settings.PROXY_USERNAME and settings.PROXY_PASSWORD:
                    proxy_config.update({
                        "username": settings.PROXY_USERNAME,
                        "password": settings.PROXY_PASSWORD
                    })
            else:
                proxy_config = None
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=browser_args,
                proxy=proxy_config
            )
            
            # 创建上下文
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": settings.DOUYIN_USER_AGENT,
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai"
            }
            
            if settings.BROWSER_USER_DATA_DIR:
                context_options["storage_state"] = settings.BROWSER_USER_DATA_DIR
            
            self.context = await self.browser.new_context(**context_options)
            
            # 设置默认超时
            self.context.set_default_timeout(settings.BROWSER_TIMEOUT)
            
            self._initialized = True
            logger.info("浏览器初始化成功")
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            await self.cleanup()
            raise BrowserError(f"浏览器初始化失败: {e}")
    
    async def cleanup(self) -> None:
        """清理浏览器资源"""
        try:
            # 关闭所有登录页面
            for page in self._login_pages.values():
                if not page.is_closed():
                    await page.close()
            self._login_pages.clear()
            
            if self.page and not self.page.is_closed():
                await self.page.close()
            
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self._initialized = False
            logger.info("浏览器资源清理完成")
            
        except Exception as e:
            logger.error(f"浏览器清理失败: {e}")
    
    async def _ensure_initialized(self) -> None:
        """确保浏览器已初始化"""
        if not self._initialized:
            await self.initialize()
    
    async def _create_login_page(self) -> Page:
        """创建登录页面"""
        await self._ensure_initialized()
        
        page = await self.context.new_page()
        
        # 设置页面事件监听
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
        
        # 注入反检测脚本
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        return page
    
    async def get_qrcode(self) -> Dict[str, Any]:
        """获取登录二维码"""
        try:
            await self._ensure_initialized()
            
            # 创建新的登录页面
            page = await self._create_login_page()
            
            # 访问抖音登录页
            await page.goto("https://www.douyin.com/passport/web/login/", wait_until="networkidle")
            
            # 等待二维码加载
            await page.wait_for_selector('.login-qrcode img', timeout=10000)
            
            # 获取二维码图片
            qr_element = await page.query_selector('.login-qrcode img')
            if not qr_element:
                raise LoginError("未找到二维码元素")
            
            qr_src = await qr_element.get_attribute('src')
            if not qr_src:
                raise LoginError("二维码图片链接为空")
            
            # 生成唯一ID
            qr_uuid = f"qr_{int(datetime.now().timestamp() * 1000)}"
            
            # 保存页面引用用于状态检查
            self._login_pages[qr_uuid] = page
            
            return {
                "success": True,
                "qr_code_url": qr_src,
                "qr_uuid": qr_uuid,
                "message": "二维码获取成功"
            }
            
        except Exception as e:
            logger.error(f"获取二维码失败: {e}")
            if 'page' in locals():
                await page.close()
            return {
                "success": False,
                "message": f"获取二维码失败: {e}"
            }
    
    async def check_qrcode_status(self, qr_uuid: str) -> Dict[str, Any]:
        """检查二维码状态"""
        try:
            page = self._login_pages.get(qr_uuid)
            if not page or page.is_closed():
                return {
                    "status": "expired",
                    "message": "二维码已过期"
                }
            
            # 检查页面状态
            try:
                # 等待页面变化，短时间检查
                await page.wait_for_function(
                    "document.querySelector('.login-qrcode-status') !== null || window.location.href.includes('douyin.com')",
                    timeout=1000
                )
            except:
                # 超时表示还在等待扫码
                pass
            
            # 检查是否扫码成功跳转
            current_url = page.url
            if "douyin.com" in current_url and "passport" not in current_url:
                # 登录成功，获取cookie
                cookies = await page.context.cookies()
                await self._save_login_cookies(cookies)
                
                # 清理页面
                await page.close()
                if qr_uuid in self._login_pages:
                    del self._login_pages[qr_uuid]
                
                return {
                    "status": "confirmed",
                    "message": "登录成功",
                    "cookies": cookies
                }
            
            # 检查二维码状态
            status_element = await page.query_selector('.login-qrcode-status')
            if status_element:
                status_text = await status_element.inner_text()
                if "已扫码" in status_text or "确认" in status_text:
                    return {
                        "status": "scanned",
                        "message": "已扫码，请在手机上确认登录"
                    }
                elif "过期" in status_text or "失效" in status_text:
                    await page.close()
                    if qr_uuid in self._login_pages:
                        del self._login_pages[qr_uuid]
                    return {
                        "status": "expired",
                        "message": "二维码已过期"
                    }
            
            return {
                "status": "waiting",
                "message": "等待扫码"
            }
            
        except Exception as e:
            logger.error(f"检查二维码状态失败: {e}")
            return {
                "status": "error",
                "message": f"检查状态失败: {e}"
            }
    
    async def login_with_password(self, username: str, password: str) -> Dict[str, Any]:
        """密码登录"""
        try:
            await self._ensure_initialized()
            
            page = await self._create_login_page()
            
            # 访问登录页
            await page.goto("https://www.douyin.com/passport/web/login/", wait_until="networkidle")
            
            # 切换到密码登录
            password_tab = await page.query_selector('text="密码登录"')
            if password_tab:
                await password_tab.click()
                await page.wait_for_timeout(1000)
            
            # 输入用户名
            username_input = await page.query_selector('input[placeholder*="手机号"]')
            if not username_input:
                username_input = await page.query_selector('input[type="text"]')
            
            if username_input:
                await username_input.fill(username)
                await page.wait_for_timeout(500)
            
            # 输入密码
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
                await page.wait_for_timeout(500)
            
            # 点击登录按钮
            login_button = await page.query_selector('button[type="submit"], .login-button, text="登录"')
            if login_button:
                await login_button.click()
            
            # 等待登录结果
            try:
                await page.wait_for_function(
                    "window.location.href.includes('douyin.com') && !window.location.href.includes('passport')",
                    timeout=10000
                )
                
                # 登录成功
                cookies = await page.context.cookies()
                await self._save_login_cookies(cookies)
                
                await page.close()
                
                return {
                    "success": True,
                    "message": "登录成功",
                    "cookies": cookies
                }
                
            except:
                # 检查是否需要验证码
                captcha_element = await page.query_selector('.captcha, .verify, .slider')
                if captcha_element:
                    return {
                        "success": False,
                        "message": "需要验证码验证",
                        "require_captcha": True
                    }
                
                # 检查错误信息
                error_element = await page.query_selector('.error-msg, .login-error')
                if error_element:
                    error_text = await error_element.inner_text()
                    return {
                        "success": False,
                        "message": error_text
                    }
                
                return {
                    "success": False,
                    "message": "登录失败，请检查用户名和密码"
                }
                
        except Exception as e:
            logger.error(f"密码登录失败: {e}")
            if 'page' in locals():
                await page.close()
            return {
                "success": False,
                "message": f"登录失败: {e}"
            }
    
    async def _save_login_cookies(self, cookies: List[Dict]) -> None:
        """保存登录Cookie"""
        try:
            # 创建存储目录
            storage_dir = "data/sessions"
            os.makedirs(storage_dir, exist_ok=True)
            
            # 保存cookie到文件
            cookie_file = os.path.join(storage_dir, "douyin_cookies.json")
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cookie保存成功: {len(cookies)} 个")
            
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
    
    async def load_cookies_from_file(self, cookie_file: str = None) -> List[Dict]:
        """从文件加载Cookie"""
        try:
            if not cookie_file:
                cookie_file = "data/sessions/douyin_cookies.json"
            
            if not os.path.exists(cookie_file):
                logger.warning(f"Cookie文件不存在: {cookie_file}")
                return []
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            logger.info(f"Cookie加载成功: {len(cookies)} 个")
            return cookies
            
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return []
    
    async def set_cookies(self, cookies: List[Dict]) -> None:
        """设置Cookie到浏览器"""
        try:
            await self._ensure_initialized()
            await self.context.add_cookies(cookies)
            logger.info("Cookie设置成功")
            
        except Exception as e:
            logger.error(f"设置Cookie失败: {e}")
    
    async def login_with_cookies(self, cookie_file: str = None) -> Dict[str, Any]:
        """使用Cookie登录"""
        try:
            await self._ensure_initialized()
            
            # 加载Cookie
            cookies = await self.load_cookies_from_file(cookie_file)
            if not cookies:
                return {
                    "success": False,
                    "message": "Cookie文件不存在或为空"
                }
            
            # 设置Cookie
            await self.set_cookies(cookies)
            
            # 验证登录状态
            is_valid = await self.validate_login_status()
            
            if is_valid:
                # 获取用户信息
                user_info = await self.get_user_info()
                return {
                    "success": True,
                    "message": "Cookie登录成功",
                    "user_info": user_info,
                    "cookies": cookies
                }
            else:
                return {
                    "success": False,
                    "message": "Cookie已失效或无效"
                }
                
        except Exception as e:
            logger.error(f"Cookie登录失败: {e}")
            return {
                "success": False,
                "message": f"Cookie登录失败: {e}"
            }

    async def validate_login_status(self) -> bool:
        """验证登录状态"""
        try:
            await self._ensure_initialized()
            
            page = await self.context.new_page()
            
            # 使用更短的超时时间，如果网络有问题就快速失败
            try:
                await page.goto("https://www.douyin.com/user/self", wait_until="load", timeout=10000)
            except:
                # 如果访问失败，可能是网络问题，尝试访问主页
                try:
                    await page.goto("https://www.douyin.com", wait_until="load", timeout=10000)
                    await page.close()
                    return False  # 无法访问用户页面，认为未登录
                except:
                    await page.close()
                    return False  # 完全无法访问
            
            # 检查是否跳转到登录页
            current_url = page.url
            if "passport" in current_url or "login" in current_url:
                await page.close()
                return False
            
            # 检查用户信息元素
            await page.wait_for_timeout(2000)  # 等待页面加载
            user_element = await page.query_selector('.user-info, .profile, .nickname, .username, h1')
            result = user_element is not None
            
            await page.close()
            return result
            
        except Exception as e:
            logger.error(f"验证登录状态失败: {e}")
            return False
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取当前登录用户信息"""
        try:
            await self._ensure_initialized()
            
            page = await self.context.new_page()
            await page.goto("https://www.douyin.com/user/self", wait_until="networkidle")
            
            if "passport" in page.url:
                await page.close()
                return None
            
            # 获取用户信息
            user_info = {}
            
            # 用户名
            nickname_element = await page.query_selector('.nickname, .username')
            if nickname_element:
                user_info["nickname"] = await nickname_element.inner_text()
            
            # 头像
            avatar_element = await page.query_selector('.avatar img')
            if avatar_element:
                user_info["avatar_url"] = await avatar_element.get_attribute('src')
            
            # 粉丝数等统计信息
            stats_elements = await page.query_selector_all('.count-item')
            for element in stats_elements:
                label = await element.query_selector('.label')
                count = await element.query_selector('.count')
                if label and count:
                    label_text = await label.inner_text()
                    count_text = await count.inner_text()
                    if "关注" in label_text:
                        user_info["following_count"] = self._parse_count(count_text)
                    elif "粉丝" in label_text:
                        user_info["follower_count"] = self._parse_count(count_text)
                    elif "获赞" in label_text:
                        user_info["like_count"] = self._parse_count(count_text)
            
            await page.close()
            return user_info if user_info else None
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            if 'page' in locals():
                await page.close()
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """解析数量字符串"""
        try:
            count_text = count_text.strip()
            if "万" in count_text:
                return int(float(count_text.replace("万", "")) * 10000)
            elif "千" in count_text:
                return int(float(count_text.replace("千", "")) * 1000)
            else:
                return int(count_text)
        except:
            return 0
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()
