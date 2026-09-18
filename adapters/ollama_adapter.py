from core.adapter import BaseAdapter, AgentSpec
import aiohttp, json

class OllamaAdapter(BaseAdapter):
    async def execute(self, task, context):
        prompt = task.get("prompt") or task.get("description") or str(task)
        base_url = self.spec.config.get("base_url", "http://localhost:11434")
        model = self.spec.config.get("model", "llama3.1")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/api/generate", json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }, timeout=aiohttp.ClientTimeout(total=self.spec.timeout_sec)) as resp:
                    data = await resp.json()
                    return {"success": True, "output": data.get("response", ""), "artifacts": [], "logs": [prompt]}
        except Exception as e:
            # Fallback: if Ollama not running, simulate with clear error (no fake outputs per spec)
            return {"success": False, "output": None, "error": f"Ollama not available: {e}", "artifacts": []}