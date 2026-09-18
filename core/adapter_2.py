"""
SPECTRE Common Agent Adapter - Every agent/tool connects through this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import time

class AgentCapability(str, Enum):
    REASONING = "reasoning"
    RESEARCH = "research"
    CODING = "coding"
    BROWSER = "browser"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    VISION = "vision"
    AUDIO = "audio"
    VIDEO = "video"
    GIT = "git"

class AgentCostTier(str, Enum):
    LOCAL_FREE = "local_free"
    OSS_HOSTED = "oss_hosted"
    FREE_TIER_API = "free_tier"
    PAID = "paid"

@dataclass
class AgentHealth:
    status: str = "unknown"
    last_check: float = 0
    latency_ms: int = 0
    error_rate: float = 0.0
    availability: str = "unknown"

@dataclass
class AgentSpec:
    id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    cost_tier: AgentCostTier
    adapter_class: str
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    availability: str = "unknown"
    health: AgentHealth = field(default_factory=AgentHealth)
    timeout_sec: int = 120
    retry_policy: Dict = field(default_factory=lambda: {"max_retries": 2, "backoff": "exponential"})
    validation_rules: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    version: str = "1.0.0"

class BaseAdapter(ABC):
    def __init__(self, spec: AgentSpec):
        self.spec = spec
        self._health = spec.health

    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def health_check(self) -> AgentHealth:
        start = time.time()
        try:
            await self.execute({"type": "health_check"}, {})
            self._health.status = "healthy"
            self._health.availability = "available"
        except Exception as e:
            self._health.status = "down"
            self._health.availability = "unavailable"
        self._health.last_check = time.time()
        self._health.latency_ms = int((time.time() - start)*1000)
        return self._health

    def validate_output(self, output: Dict) -> bool:
        if not output.get("success"):
            return False
        return True
