"""
MCP服务器核心实现
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
import uvicorn

from .tool_registry import tool_registry, ToolDefinition, ToolParameter
from .exceptions import MCPError, ValidationError
from ..config.settings import settings


class MCPRequest(BaseModel):
    """MCP请求模型"""
    tool: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """MCP响应模型"""
    success: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: Optional[float] = None


class ToolInfo(BaseModel):
    """工具信息模型"""
    name: str
    description: str
    category: str
    parameters: List[Dict[str, Any]]


class ServerStatus(BaseModel):
    """服务器状态模型"""
    status: str
    version: str
    uptime: float
    registered_tools: int
    categories: List[str]


class MCPServer:
    """MCP服务器主类"""
    
    def __init__(self, name: str = "douyin-lawyer-mcp", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.start_time = datetime.now()
        self.app = FastAPI(
            title=name,
            description="抖音律师MCP工具服务器",
            version=version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"MCP服务器 {name} v{version} 初始化完成")
    
    def _register_routes(self) -> None:
        """注册API路由"""
        
        @self.app.get("/", response_model=Dict[str, Any])
        async def root():
            """根路径 - 服务器信息"""
            return {
                "name": self.name,
                "version": self.version,
                "description": "抖音律师MCP工具服务器",
                "status": "running",
                "docs_url": "/docs"
            }
        
        @self.app.get("/status", response_model=ServerStatus)
        async def get_status():
            """获取服务器状态"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            return ServerStatus(
                status="running",
                version=self.version,
                uptime=uptime,
                registered_tools=len(tool_registry.tools),
                categories=tool_registry.list_categories()
            )
        
        @self.app.get("/tools", response_model=List[ToolInfo])
        async def list_tools(category: Optional[str] = None):
            """列出所有工具"""
            try:
                tools = tool_registry.list_tools(category)
                tool_infos = []
                
                for tool in tools:
                    parameters = []
                    for param in tool.parameters:
                        param_info = {
                            "name": param.name,
                            "type": param.type,
                            "description": param.description,
                            "required": param.required
                        }
                        if param.default is not None:
                            param_info["default"] = param.default
                        if param.enum:
                            param_info["enum"] = param.enum
                        parameters.append(param_info)
                    
                    tool_infos.append(ToolInfo(
                        name=tool.name,
                        description=tool.description,
                        category=tool.category,
                        parameters=parameters
                    ))
                
                return tool_infos
                
            except Exception as e:
                logger.error(f"获取工具列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tools/{tool_name}", response_model=ToolInfo)
        async def get_tool(tool_name: str):
            """获取特定工具信息"""
            try:
                tool = tool_registry.get_tool(tool_name)
                if not tool:
                    raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
                
                parameters = []
                for param in tool.parameters:
                    param_info = {
                        "name": param.name,
                        "type": param.type,
                        "description": param.description,
                        "required": param.required
                    }
                    if param.default is not None:
                        param_info["default"] = param.default
                    if param.enum:
                        param_info["enum"] = param.enum
                    parameters.append(param_info)
                
                return ToolInfo(
                    name=tool.name,
                    description=tool.description,
                    category=tool.category,
                    parameters=parameters
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取工具 {tool_name} 信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/execute", response_model=MCPResponse)
        async def execute_tool(request: MCPRequest, background_tasks: BackgroundTasks):
            """执行工具"""
            start_time = datetime.now()
            
            try:
                logger.info(f"执行工具请求: {request.tool}")
                
                # 验证工具是否存在
                tool = tool_registry.get_tool(request.tool)
                if not tool:
                    raise HTTPException(status_code=404, detail=f"工具 {request.tool} 不存在")
                
                # 执行工具
                result = await tool_registry.execute_tool(request.tool, request.parameters)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"工具 {request.tool} 执行成功，耗时: {execution_time:.2f}s")
                
                return MCPResponse(
                    success=True,
                    result=result,
                    execution_time=execution_time
                )
                
            except HTTPException:
                raise
            except MCPError as e:
                logger.error(f"MCP错误: {e}")
                execution_time = (datetime.now() - start_time).total_seconds()
                return MCPResponse(
                    success=False,
                    error=e.to_dict(),
                    execution_time=execution_time
                )
            except Exception as e:
                logger.error(f"执行工具 {request.tool} 失败: {e}")
                execution_time = (datetime.now() - start_time).total_seconds()
                return MCPResponse(
                    success=False,
                    error={
                        "error_code": "EXECUTION_ERROR",
                        "message": str(e),
                        "details": {}
                    },
                    execution_time=execution_time
                )
        
        @self.app.get("/categories", response_model=List[str])
        async def list_categories():
            """列出所有工具分类"""
            return tool_registry.list_categories()
        
        @self.app.get("/mcp/tools", response_model=List[Dict[str, Any]])
        async def get_mcp_tools():
            """获取MCP格式的工具定义"""
            return tool_registry.to_mcp_tools()
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now()}
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """注册工具"""
        tool_registry.register_tool(tool)
    
    def register_tools(self, tools: List[ToolDefinition]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register_tool(tool)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        """启动服务器"""
        try:
            logger.info(f"启动MCP服务器: {host}:{port}")
            
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level=settings.LOG_LEVEL.lower(),
                **kwargs
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            raise
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        """同步方式启动服务器"""
        try:
            uvicorn.run(
                app=self.app,
                host=host,
                port=port,
                log_level=settings.LOG_LEVEL.lower(),
                **kwargs
            )
        except Exception as e:
            logger.error(f"运行服务器失败: {e}")
            raise


# 全局MCP服务器实例
mcp_server = MCPServer()
