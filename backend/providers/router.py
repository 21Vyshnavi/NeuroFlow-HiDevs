# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import json

import redis.asyncio as redis
from pydantic import BaseModel

from backend.config import settings


class RoutingCriteria(BaseModel):
    task_type: str          # "rag_generation" | "evaluation" | "embedding" | "classification"
    max_cost_per_call: float | None = None
    require_vision: bool = False
    require_long_context: bool = False  # > 32k tokens
    latency_budget_ms: int | None = None
    prefer_fine_tuned: bool = False

class ModelConfig(BaseModel):
    model_name: str
    provider: str  # "openai" | "anthropic"
    is_vision: bool
    context_limit: int
    estimated_input_cost: float   # per 1M tokens
    estimated_output_cost: float  # per 1M tokens
    is_fine_tuned: bool = False
    task_type: str | None = None

class ModelRouter:
    def __init__(self) -> None:
        # Default fallback models if Redis is empty
        self.default_models = [
            ModelConfig(
                model_name="gpt-4o-mini",
                provider="openai",
                is_vision=True,
                context_limit=128000,
                estimated_input_cost=0.15,
                estimated_output_cost=0.60
            ),
            ModelConfig(
                model_name="gpt-4o",
                provider="openai",
                is_vision=True,
                context_limit=128000,
                estimated_input_cost=2.50,
                estimated_output_cost=10.00
            ),
            ModelConfig(
                model_name="claude-3-haiku-20240307",
                provider="anthropic",
                is_vision=False,
                context_limit=200000,
                estimated_input_cost=0.25,
                estimated_output_cost=1.25
            ),
            ModelConfig(
                model_name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                is_vision=True,
                context_limit=200000,
                estimated_input_cost=3.00,
                estimated_output_cost=15.00
            )
        ]

    async def get_models(self) -> list[ModelConfig]:
        try:
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                socket_connect_timeout=2
            )
            data = await r.get("router:models")
            await r.aclose()
            if data:
                configs = json.loads(data)
                return [ModelConfig(**c) for c in configs]
        except Exception:
            pass
        return self.default_models

    async def route(self, criteria: RoutingCriteria) -> ModelConfig:
        models = await self.get_models()
        
        # Hard Constraints Filter
        filtered = []
        for m in models:
            # 1. Vision requirement
            if criteria.require_vision and not m.is_vision:
                continue
            # 2. Long context requirement (>32k)
            if criteria.require_long_context and m.context_limit <= 32000:
                continue
            # 3. Cost constraint estimation (based on a typical 1000 input, 500 output token generation)
            if criteria.max_cost_per_call is not None:
                estimated_cost = (1000 * (m.estimated_input_cost / 1_000_000.0)) + (500 * (m.estimated_output_cost / 1_000_000.0))
                if estimated_cost > criteria.max_cost_per_call:
                    continue
            filtered.append(m)

        if not filtered:
            # Fallback to absolute default if everything was filtered out
            filtered = self.default_models

        # 4. Evaluation rule: always use high quality models, never fine-tuned
        if criteria.task_type == "evaluation":
            # Prefer sonnet or gpt-4o
            for name in ["claude-3-5-sonnet-20241022", "gpt-4o"]:
                for m in filtered:
                    if m.model_name == name:
                        return m
            return filtered[1] # fallback to gpt-4o

        # 5. Fine-tuned preference
        if criteria.prefer_fine_tuned:
            ft_models = [m for m in filtered if m.is_fine_tuned and m.task_type == criteria.task_type]
            if ft_models:
                return ft_models[0]

        # 6. Default: route to cheapest model (sum of input + output estimation)
        filtered.sort(key=lambda m: m.estimated_input_cost + m.estimated_output_cost)
        return filtered[0]
