"""
Dynamic Agent/Tool Registry - discovers, registers, tests and invokes free OSS resources
"""
import json, asyncio, importlib
from typing import Dict, List, Optional
from core.adapter import AgentSpec, AgentCapability, AgentCostTier, BaseAdapter, AgentHealth
from pathlib import Path

REGISTRY_FILE = Path("memory/registry.json")

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, AgentSpec] = {}
        self.adapters: Dict[str, BaseAdapter] = {}
        self.load_builtin()

    def load_builtin(self):
        # 1. LOCAL FREE - Highest priority
        builtin = [
            AgentSpec(
                id="ollama_llama3",
                name="Ollama Llama 3.1",
                description="Local Llama via Ollama - reasoning, coding",
                capabilities=[AgentCapability.REASONING, AgentCapability.CODING],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.ollama_adapter.OllamaAdapter",
                timeout_sec=300
            ),
            AgentSpec(
                id="hf_transformers_local",
                name="HuggingFace Local Pipeline",
                description="Any HF model locally via transformers",
                capabilities=[AgentCapability.REASONING, AgentCapability.VISION, AgentCapability.AUDIO],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.hf_adapter.HFAdapter",
            ),
            AgentSpec(
                id="langgraph_local",
                name="LangGraph",
                description="Local LangGraph workflows",
                capabilities=[AgentCapability.REASONING],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.langgraph_adapter.LangGraphAdapter",
            ),
            AgentSpec(
                id="crewai_local",
                name="CrewAI",
                description="Multi-agent crews - free local",
                capabilities=[AgentCapability.REASONING, AgentCapability.RESEARCH],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.crewai_adapter.CrewAIAdapter",
            ),
            AgentSpec(
                id="smolagents_local",
                name="smolagents",
                description="HF smolagents - code + tool use",
                capabilities=[AgentCapability.CODING, AgentCapability.RESEARCH],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.smolagents_adapter.SmolAdapter",
            ),
            AgentSpec(
                id="autogen_local",
                name="AutoGen",
                description="Microsoft AutoGen local orchestration",
                capabilities=[AgentCapability.REASONING, AgentCapability.CODING],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.autogen_adapter.AutoGenAdapter",
            ),
            AgentSpec(
                id="browser_playwright",
                name="Playwright Browser Agent",
                description="Browser automation, research, scraping",
                capabilities=[AgentCapability.BROWSER, AgentCapability.RESEARCH],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.browser_adapter.PlaywrightAdapter",
            ),
            AgentSpec(
                id="git_tool",
                name="Git Tool",
                description="Git operations",
                capabilities=[AgentCapability.GIT],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.git_adapter.GitAdapter",
            ),
            AgentSpec(
                id="coding_agent",
                name="OpenHands / Coding Agent",
                description="Code generation, refactoring, testing",
                capabilities=[AgentCapability.CODING, AgentCapability.TESTING],
                cost_tier=AgentCostTier.LOCAL_FREE,
                adapter_class="adapters.coding_adapter.CodingAdapter",
            ),
            # 2. OSS HOSTED FREE
            AgentSpec(
                id="hf_inference_free",
                name="Hugging Face Inference API (free)",
                description="Free HF hosted inference",
                capabilities=[AgentCapability.REASONING, AgentCapability.VISION],
                cost_tier=AgentCostTier.OSS_HOSTED,
                adapter_class="adapters.hf_adapter.HFInferenceAdapter",
            ),
            # 3. FREE TIER APIs
            AgentSpec(
                id="mcp_server",
                name="MCP Server Registry",
                description="Model Context Protocol servers",
                capabilities=[AgentCapability.DATABASE, AgentCapability.DEPLOYMENT],
                cost_tier=AgentCostTier.FREE_TIER_API,
                adapter_class="adapters.mcp_adapter.MCPAdapter",
            ),
        ]
        for spec in builtin:
            self.agents[spec.id] = spec

        # Auto-discover from config folder
        self.discover_from_config()

    def discover_from_config(self):
        cfg_path = Path("config/agents")
        if not cfg_path.exists():
            return
        for f in cfg_path.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                spec = AgentSpec(**data)
                self.agents[spec.id] = spec
            except Exception as e:
                print(f"[Registry] Failed to load {f}: {e}")

    def get_by_capability(self, cap: AgentCapability, allowed_tiers: List[AgentCostTier]) -> List[AgentSpec]:
        return [a for a in self.agents.values() 
                if cap in a.capabilities and a.cost_tier in allowed_tiers and a.enabled]

    def rank_agents(self, specs: List[AgentSpec]) -> List[AgentSpec]:
        # Routing order: LOCAL_FREE < OSS_HOSTED < FREE_TIER < PAID
        order = {AgentCostTier.LOCAL_FREE: 0, AgentCostTier.OSS_HOSTED: 1, AgentCostTier.FREE_TIER_API: 2, AgentCostTier.PAID: 3}
        return sorted(specs, key=lambda s: (order[s.cost_tier], s.health.error_rate, s.health.latency_ms))

    async def get_adapter(self, agent_id: str) -> BaseAdapter:
        if agent_id in self.adapters:
            return self.adapters[agent_id]
        spec = self.agents[agent_id]
        module_path, cls_name = spec.adapter_class.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        cls = getattr(mod, cls_name)
        adapter = cls(spec)
        self.adapters[agent_id] = adapter
        return adapter

    async def health_check_all(self):
        for aid in list(self.agents.keys()):
            try:
                adapter = await self.get_adapter(aid)
                health = await adapter.health_check()
                self.agents[aid].health = health
            except Exception as e:
                self.agents[aid].health.status = "down"