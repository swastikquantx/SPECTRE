from core.adapter import BaseAdapter
class LangGraphAdapter(BaseAdapter):
    async def execute(self, task, context):
        # Placeholder - requires pip install langgraph
        # To activate: pip install langgraph
        return {"success": False, "error": "Dependency not installed", "output": None}