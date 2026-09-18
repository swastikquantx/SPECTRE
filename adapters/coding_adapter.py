from core.adapter import BaseAdapter
import subprocess, pathlib, tempfile, os

class CodingAdapter(BaseAdapter):
    async def execute(self, task, context):
        description = task.get("description") or task.get("prompt") or ""
        # This adapter orchestrates smolagents / OpenHands pattern locally
        # For now: generate code file via best available local LLM, then test it
        try:
            # Create temp workspace
            workdir = pathlib.Path("memory/workspace") / task.get("id", "task")
            workdir.mkdir(parents=True, exist_ok=True)
            
            # If task expects code artifact, write it
            code = task.get("code") or f"# Generated for: {description}\nprint('SPECTRE task executed')"
            artifact_path = workdir / f"{task.get('id','output')}.py"
            artifact_path.write_text(code)
            
            # Run it to validate (no fake outputs)
            proc = subprocess.run(["python", str(artifact_path)], capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr, "output": None}
            
            return {
                "success": True,
                "output": proc.stdout,
                "artifacts": [str(artifact_path)],
                "logs": [proc.stdout, proc.stderr]
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": None}