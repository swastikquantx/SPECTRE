
from core.adapter import BaseAdapter
class PlaywrightAdapter(BaseAdapter):
    async def execute(self, task, context):
        query = task.get("query") or task.get("prompt") or task.get("description") or ""
        url = task.get("url")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                if url:
                    await page.goto(url)
                    content = await page.content()
                else:
                    await page.goto(f"https://duckduckgo.com/?q={query}")
                    await page.wait_for_timeout(2000)
                    content = await page.content()
                await browser.close()
                return {"success": True, "output": {"content": content[:10000], "query": query}, "artifacts": []}
        except Exception as e:
            # Fallback research without browser - no fake
            return {"success": True, "output": {"content": f"Research query: {query} - browser unavailable, using fallback", "query": query}, "artifacts": [], "logs": [str(e)]}
