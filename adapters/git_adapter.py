from core.adapter import BaseAdapter
class GitAdapter(BaseAdapter):
    async def execute(self, task, context):
        # Placeholder - requires pip install git
        # To activate: pip install GitPython
        return {"success": False, "error": "Dependency not installed", "output": None}