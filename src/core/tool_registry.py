"""
MCP工具注册表 - 管理所有可用的工具
"""

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger

from .exceptions import MCPError


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter]
    category: str = "general"
    handler: Optional[Callable] = None
    
    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[str, List[str]] = {}
        logger.info("工具注册表初始化完成")
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """注册工具"""
        try:
            if tool.name in self.tools:
                logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
            
            self.tools[tool.name] = tool
            
            # 更新分类
            if tool.category not in self.categories:
                self.categories[tool.category] = []
            
            if tool.name not in self.categories[tool.category]:
                self.categories[tool.category].append(tool.name)
            
            logger.info(f"工具 {tool.name} 注册成功，分类: {tool.category}")
            
        except Exception as e:
            logger.error(f"注册工具 {tool.name} 失败: {e}")
            raise MCPError(f"工具注册失败: {e}")
    
    def unregister_tool(self, tool_name: str) -> None:
        """注销工具"""
        try:
            if tool_name not in self.tools:
                raise MCPError(f"工具 {tool_name} 不存在")
            
            tool = self.tools[tool_name]
            del self.tools[tool_name]
            
            # 从分类中移除
            if tool.category in self.categories:
                if tool_name in self.categories[tool.category]:
                    self.categories[tool.category].remove(tool_name)
                
                # 如果分类为空，删除分类
                if not self.categories[tool.category]:
                    del self.categories[tool.category]
            
            logger.info(f"工具 {tool_name} 注销成功")
            
        except Exception as e:
            logger.error(f"注销工具 {tool_name} 失败: {e}")
            raise MCPError(f"工具注销失败: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self.tools.get(tool_name)
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """根据分类获取工具"""
        if category not in self.categories:
            return []
        
        return [self.tools[name] for name in self.categories[category]]
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """列出所有工具"""
        if category:
            return self.get_tools_by_category(category)
        
        return list(self.tools.values())
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return list(self.categories.keys())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行工具"""
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                raise MCPError(f"工具 {tool_name} 不存在")
            
            if not tool.handler:
                raise MCPError(f"工具 {tool_name} 没有处理函数")
            
            # 验证参数
            self._validate_parameters(tool, parameters)
            
            # 执行工具
            logger.info(f"开始执行工具: {tool_name}")
            result = await tool.handler(**parameters)
            logger.info(f"工具 {tool_name} 执行完成")
            
            return result
            
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            raise MCPError(f"工具执行失败: {e}")
    
    def _validate_parameters(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> None:
        """验证参数"""
        # 检查必需参数
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                raise MCPError(f"缺少必需参数: {param.name}")
        
        # 检查参数类型和值
        for param_name, param_value in parameters.items():
            param_def = next((p for p in tool.parameters if p.name == param_name), None)
            if not param_def:
                logger.warning(f"未知参数: {param_name}")
                continue
            
            # 检查枚举值
            if param_def.enum and param_value not in param_def.enum:
                raise MCPError(f"参数 {param_name} 的值 {param_value} 不在允许的枚举值中: {param_def.enum}")
    
    def to_mcp_tools(self) -> List[Dict[str, Any]]:
        """转换为MCP工具格式"""
        mcp_tools = []
        
        for tool in self.tools.values():
            properties = {}
            required = []
            
            for param in tool.parameters:
                param_schema = {
                    "type": param.type,
                    "description": param.description
                }
                
                if param.enum:
                    param_schema["enum"] = param.enum
                
                if param.default is not None:
                    param_schema["default"] = param.default
                
                properties[param.name] = param_schema
                
                if param.required:
                    required.append(param.name)
            
            mcp_tool = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
            mcp_tools.append(mcp_tool)
        
        return mcp_tools


# 全局工具注册表实例
tool_registry = ToolRegistry()
