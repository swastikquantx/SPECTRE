
from core.adapter import BaseAdapter
class HFAdapter(BaseAdapter):
    async def execute(self, task, context):
        try:
            from transformers import pipeline
            model_id = self.spec.config.get("model_id", "microsoft/DialoGPT-medium")
            task_type = self.spec.config.get("task", "text-generation")
            pipe = pipeline(task_type, model=model_id)
            prompt = task.get("prompt") or task.get("description") or ""
            result = pipe(prompt, max_new_tokens=512)
            output = result[0].get("generated_text") if result else str(result)
            return {"success": True, "output": output, "artifacts": []}
        except Exception as e:
            return {"success": False, "error": str(e), "output": None}

class HFInferenceAdapter(BaseAdapter):
    async def execute(self, task, context):
        prompt = task.get("prompt") or task.get("description") or ""
        try:
            import aiohttp
            model_id = self.spec.config.get("model_id", "meta-llama/Meta-Llama-3-8B-Instruct")
            hf_token = self.spec.config.get("hf_token", "")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api-inference.huggingface.co/models/{model_id}",
                    headers={"Authorization": f"Bearer {hf_token}"} if hf_token else {},
                    json={"inputs": prompt},
                    timeout=aiohttp.ClientTimeout(total=self.spec.timeout_sec)
                ) as resp:
                    data = await resp.json()
                    text = data[0].get("generated_text") if isinstance(data, list) else str(data)
                    return {"success": True, "output": text, "artifacts": []}
        except Exception as e:
            return {"success": False, "error": str(e), "output": None}
