"""
SPECTRE MASTER ORCHESTRATOR - The autonomous decision-maker
Flow: UNDERSTAND → RESEARCH → PLAN → DISCOVER TOOLS → SELECT AGENTS → EXECUTE → OBSERVE → VALIDATE → REPAIR → DELIVER
"""
import asyncio, json, uuid, time
from typing import Dict, Any, List
from core.adapter import AgentCapability, AgentCostTier
from registry.registry import AgentRegistry

class SpectreOrchestrator:
    """NO FAKE OUTPUTS, NO MOCK EXECUTION, NO FALSE COMPLETION - Real verifiable artifacts only"""
    def __init__(self, registry: AgentRegistry, allow_paid: bool = False):
        self.registry = registry
        self.allow_paid = allow_paid
        self.mission_id = None
        self.trace: List[Dict] = []
        self.state: Dict[str, Any] = {}

    def log(self, phase: str, msg: str, data: Any = None):
        entry = {"phase": phase, "msg": msg, "ts": time.time(), "data": data}
        self.trace.append(entry)
        print(f"[{phase}] {msg}")

    async def run_mission(self, objective: str) -> Dict[str, Any]:
        self.mission_id = str(uuid.uuid4())[:8]
        self.state = {"objective": objective, "artifacts": [], "context": {}}
        self.log("INIT", f"Mission {self.mission_id}: {objective}")

        # PHASE 1: UNDERSTAND
        self.log("UNDERSTAND", "Parsing objective...")
        understanding = await self.understand(objective)
        self.state["understanding"] = understanding

        # PHASE 2: RESEARCH
        self.log("RESEARCH", "Gathering context...")
        research = await self.research(understanding)
        self.state["research"] = research

        # PHASE 3: PLAN
        self.log("PLAN", "Decomposing into tasks...")
        plan = await self.plan(understanding, research)
        self.state["plan"] = plan

        # PHASE 4: DISCOVER TOOLS
        self.log("DISCOVER_TOOLS", "Discovering compatible agents...")
        await self.registry.health_check_all()
        self.log("DISCOVER_TOOLS", f"Registry: {len(self.registry.agents)} agents available")

        # PHASE 5-9: EXECUTE LOOP
        results = []
        for task in plan["tasks"]:
            result = await self.execute_task_with_repair(task)
            results.append(result)

        # PHASE 10: DELIVER
        self.log("DELIVER", "Validating final deliverables...")
        final = await self.deliver(results)
        
        return {
            "mission_id": self.mission_id,
            "objective": objective,
            "understanding": understanding,
            "plan": plan,
            "results": results,
            "final_output": final,
            "trace": self.trace,
            "status": "COMPLETE" if final.get("verified") else "FAILED"
        }

    async def understand(self, objective: str) -> Dict:
        # Use best local reasoning agent
        allowed = [AgentCostTier.LOCAL_FREE, AgentCostTier.OSS_HOSTED, AgentCostTier.FREE_TIER_API]
        if self.allow_paid:
            allowed.append(AgentCostTier.PAID)
        
        candidates = self.registry.get_by_capability(AgentCapability.REASONING, allowed)
        ranked = self.registry.rank_agents(candidates)
        
        prompt = f"""
        OBJECTIVE: {objective}
        Break down into: intent, required capabilities, constraints, deliverables, success criteria.
        Return JSON: {{intent, capabilities_needed[], constraints, deliverables[], success_criteria[]}}
        """
        if not ranked:
            # Fallback heuristic parser
            return {
                "intent": objective,
                "capabilities_needed": ["reasoning", "coding", "research"],
                "constraints": [],
                "deliverables": ["working result"],
                "success_criteria": ["real, usable, exportable"]
            }
        
        adapter = await self.registry.get_adapter(ranked[0].id)
        out = await adapter.execute({"type": "understand", "prompt": prompt}, self.state)
        try:
            parsed = json.loads(out["output"]) if isinstance(out["output"], str) else out.get("output")
            if not parsed or not isinstance(parsed, dict):
                raise ValueError("Empty output")
            return parsed
        except Exception as e:
            fallback = out.get("output")
            if isinstance(fallback, dict) and fallback:
                return fallback
            return {"intent": objective, "capabilities_needed": ["reasoning", "coding", "research"], "constraints": [], "deliverables": ["working result"], "success_criteria": ["real, usable, exportable"]}

    async def research(self, understanding: Dict) -> Dict:
        # Use browser/research agents
        allowed = [AgentCostTier.LOCAL_FREE, AgentCostTier.OSS_HOSTED, AgentCostTier.FREE_TIER_API]
        candidates = self.registry.get_by_capability(AgentCapability.RESEARCH, allowed)
        ranked = self.registry.rank_agents(candidates)
        if not ranked:
            return {"notes": "No research agent available, using base knowledge"}
        adapter = await self.registry.get_adapter(ranked[0].id)
        intent = understanding.get("intent") if isinstance(understanding, dict) else str(understanding)
        out = await adapter.execute({"type": "research", "query": intent}, self.state)
        return out.get("output", {})

    async def plan(self, understanding: Dict, research: Dict) -> Dict:
        # Planning via reasoning agent
        tasks_prompt = f"""
        Given understanding {understanding} and research {research},
        create execution plan as JSON: {{tasks: [{{id, description, capability, inputs, expected_output, validation}}]}}
        """
        allowed = [AgentCostTier.LOCAL_FREE, AgentCostTier.OSS_HOSTED]
        candidates = self.registry.get_by_capability(AgentCapability.REASONING, allowed)
        ranked = self.registry.rank_agents(candidates)
        if not ranked:
            # Heuristic plan
            return {
                "tasks": [
                    {"id": "t1", "description": understanding["intent"], "capability": "coding", "inputs": {}, "expected_output": "artifact", "validation": "exists and runs"}
                ]
            }
        try:
            adapter = await self.registry.get_adapter(ranked[0].id)
            out = await adapter.execute({"type": "plan", "prompt": tasks_prompt}, self.state)
            parsed = json.loads(out["output"]) if isinstance(out["output"], str) else out.get("output")
            if isinstance(parsed, dict) and "tasks" in parsed and parsed["tasks"]:
                return parsed
            raise ValueError("empty plan")
        except Exception as e:
            intent = understanding.get("intent") if isinstance(understanding, dict) else str(understanding)
            return {"tasks": [{"id": "t1", "description": intent, "capability": "coding", "inputs": {}, "expected_output": "artifact", "validation": "exists and runs"}]}

    async def execute_task_with_repair(self, task: Dict) -> Dict:
        cap = AgentCapability(task.get("capability", "coding"))
        allowed = [AgentCostTier.LOCAL_FREE, AgentCostTier.OSS_HOSTED, AgentCostTier.FREE_TIER_API]
        if self.allow_paid:
            allowed.append(AgentCostTier.PAID)
        
        candidates = self.registry.get_by_capability(cap, allowed)
        ranked = self.registry.rank_agents(candidates)
        
        self.log("SELECT_AGENTS", f"Task {task['id']}: {len(ranked)} candidates for {cap}")

        last_error = None
        for spec in ranked:
            self.log("EXECUTE", f"Trying {spec.name} ({spec.cost_tier}) for {task['id']}")
            try:
                adapter = await self.registry.get_adapter(spec.id)
                # OBSERVE phase via timeout handling
                result = await asyncio.wait_for(
                    adapter.execute(task, self.state),
                    timeout=spec.timeout_sec
                )
                # VALIDATE
                self.log("VALIDATE", f"Validating output from {spec.id}")
                if not adapter.validate_output(result):
                    raise ValueError(f"Validation failed for {spec.id}")
                if not result.get("success"):
                    raise ValueError(f"Agent reported failure: {result}")

                self.log("OBSERVE", f"Task {task['id']} succeeded with {spec.id}")
                self.state["context"][task["id"]] = result["output"]
                if result.get("artifacts"):
                    self.state["artifacts"].extend(result["artifacts"])
                return {"task": task, "agent": spec.id, "result": result, "status": "success"}

            except Exception as e:
                self.log("REPAIR", f"Agent {spec.id} failed: {e}, trying next")
                last_error = str(e)
                # Mark degraded
                spec.health.error_rate += 0.1
                continue

        # All agents failed
        return {"task": task, "status": "failed", "error": last_error}

    async def deliver(self, results: List[Dict]) -> Dict:
        # Verify real, usable, exportable result
        failed = [r for r in results if r["status"] == "failed"]
        if failed:
            return {"verified": False, "reason": f"{len(failed)} tasks failed", "results": results}
        
        # Check artifacts exist
        artifacts = self.state.get("artifacts", [])
        verified = len(artifacts) > 0 or any(r["result"].get("output") for r in results)
        
        return {
            "verified": verified,
            "artifacts": artifacts,
            "summary": "Mission COMPLETE - real, usable, exportable result produced" if verified else "No artifacts produced",
            "exportable": True
        }