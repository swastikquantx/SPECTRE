from core.adapter import BaseAdapter
class MCPAdapter(BaseAdapter):
    async def execute(self, task, context):
        # Placeholder - requires pip install mcp
        # To activate: pip install mcp
        return {"success": False, "error": "Dependency not installed", "output": None}