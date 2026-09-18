
"""
SPECTRE MASTER SERVER - FastAPI
Implements the autonomous loop as API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from registry.registry import AgentRegistry
from core.orchestrator import SpectreOrchestrator

app = FastAPI(title="SPECTRE MASTER AI AGENT", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

registry = AgentRegistry()

class ObjectiveRequest(BaseModel):
    objective: str
    allow_paid: bool = False

class AgentRegisterRequest(BaseModel):
    id: str
    name: str
    description: str
    capabilities: list
    cost_tier: str = "local_free"
    adapter_class: str
    config: dict = {}

@app.get("/")
def root():
    return {"agent": "SPECTRE", "status": "MASTER ORCHESTRATOR ACTIVE", "agents": len(registry.agents), "routing_order": ["local_free", "oss_hosted", "free_tier", "paid(if enabled)"]}

@app.get("/registry")
def get_registry():
    return {aid: {"name": spec.name, "capabilities": [c.value for c in spec.capabilities], "tier": spec.cost_tier.value, "status": spec.health.status, "enabled": spec.enabled} for aid, spec in registry.agents.items()}

@app.post("/registry/register")
def register_agent(req: AgentRegisterRequest):
    from core.adapter import AgentSpec, AgentCapability, AgentCostTier
    spec = AgentSpec(
        id=req.id,
        name=req.name,
        description=req.description,
        capabilities=[AgentCapability(c) for c in req.capabilities],
        cost_tier=AgentCostTier(req.cost_tier),
        adapter_class=req.adapter_class,
        config=req.config
    )
    registry.agents[spec.id] = spec
    return {"success": True, "id": spec.id}

@app.post("/mission")
async def run_mission(req: ObjectiveRequest):
    orchestrator = SpectreOrchestrator(registry, allow_paid=req.allow_paid)
    try:
        result = await orchestrator.run_mission(req.objective)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    await registry.health_check_all()
    return {aid: spec.health.__dict__ for aid, spec in registry.agents.items()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
